import pytest
from types import SimpleNamespace
from uuid import uuid4

from src.exceptions import InternalError, RateLimitError, ValidationError
from src.infrastructure.llm import LLMProviderError
from src.modules.named_queries.schemas import (
    NamedQueryGenerationMessage,
    TransactionPreviewFilters,
)
from src.modules.named_queries.service import NamedQueryGenerationService, NamedQueryService
from src.modules.named_queries.sql_validator import validate_named_query_sql


class FakeDbDiagnostic:
    message_primary = 'column "category_primar" does not exist'
    message_hint = (
        'Perhaps you meant to reference the column '
        '"widget_transactions.category_primary".'
    )


class FakeDbError:
    diag = FakeDbDiagnostic()


class FakeSqlAlchemyError(Exception):
    orig = FakeDbError()


class FakeUsageRepo:
    def __init__(self, usage=None):
        self.usage = usage or SimpleNamespace(
            quota_units_used=0,
            llm_calls=0,
            clarifying_questions=0,
            validation_failures=0,
            repair_attempts=0,
            generation_failures=0,
            provider_failures=0,
        )

    def get_or_create_for_date(self, db, household_id, usage_date):
        return self.usage

    def increment(self, db, usage, **counters):
        for name, amount in counters.items():
            setattr(usage, name, getattr(usage, name) + amount)
        return usage


class FakeLLMClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def generate_structured(self, *, messages, schema_name, json_schema):
        self.calls.append(messages)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _generation_service(responses, usage_repo=None, daily_quota=100, repair_attempts=2):
    return NamedQueryGenerationService(
        llm_client=FakeLLMClient(responses),
        usage_repo=usage_repo or FakeUsageRepo(),
        daily_quota=daily_quota,
        repair_attempts=repair_attempts,
    )


def _message(content="show spending by category"):
    return [NamedQueryGenerationMessage(role="member", content=content)]


def test_household_filter_is_injected_before_grouping():
    service = NamedQueryService(named_query_repo=None)

    scoped_sql = service._inject_household_filter(
        "SELECT category_primary as category, SUM(amount) AS total "
        "FROM widget_transactions "
        "GROUP BY category "
        "ORDER BY total DESC"
    )

    assert scoped_sql == (
        "SELECT category_primary AS category, SUM(amount) AS total "
        "FROM widget_transactions "
        "WHERE widget_transactions.household_id = :_household_id "
        "GROUP BY category "
        "ORDER BY total DESC"
    )


def test_household_filter_is_appended_to_existing_where_clause():
    service = NamedQueryService(named_query_repo=None)

    scoped_sql = service._inject_household_filter(
        "SELECT amount "
        "FROM widget_transactions "
        "WHERE amount > 0 "
        "ORDER BY amount DESC"
    )

    assert scoped_sql == (
        "SELECT amount "
        "FROM widget_transactions "
        "WHERE amount > 0 AND widget_transactions.household_id = :_household_id "
        "ORDER BY amount DESC"
    )


def test_household_filter_is_qualified_for_each_widget_table_alias():
    service = NamedQueryService(named_query_repo=None)

    scoped_sql = service._inject_household_filter(
        "SELECT wt.category_primary, wa.name "
        "FROM widget_transactions wt "
        "JOIN widget_accounts wa ON TRUE"
    )

    assert scoped_sql == (
        "SELECT wt.category_primary, wa.name "
        "FROM widget_transactions AS wt "
        "JOIN widget_accounts AS wa ON TRUE "
        "WHERE wt.household_id = :_household_id AND wa.household_id = :_household_id"
    )


def test_validator_returns_error_for_unterminated_string():
    result = validate_named_query_sql(
        "SELECT category_primary AS category "
        "FROM widget_transactions "
        "WHERE category_primary <> 'TRANSFER_IN"
    )

    assert result.valid is False
    assert result.error is not None
    assert result.error.startswith("SQL parse error:")


def test_household_filter_injection_returns_validation_error_for_bad_sql():
    service = NamedQueryService(named_query_repo=None)

    with pytest.raises(ValidationError, match="SQL parse error"):
        service._inject_household_filter(
            "SELECT category_primary AS category "
            "FROM widget_transactions "
            "WHERE category_primary <> 'TRANSFER_IN"
        )


def test_query_execution_error_formats_database_diagnostics():
    service = NamedQueryService(named_query_repo=None)

    message = service._format_query_execution_error(FakeSqlAlchemyError())

    assert message == (
        'Query execution failed: column "category_primar" does not exist. '
        'Perhaps you meant "widget_transactions.category_primary".'
    )


def test_query_execution_error_omits_sqlalchemy_sql_context():
    service = NamedQueryService(named_query_repo=None)
    error = Exception(
        '(psycopg.errors.UndefinedColumn) column "category_primar" does not exist\n'
        "[SQL: SELECT * FROM (...)]"
    )

    message = service._format_query_execution_error(error)

    assert message == 'Query execution failed: column "category_primar" does not exist'


def test_transaction_preview_sql_reuses_query_filters_and_joins():
    service = NamedQueryService(named_query_repo=None)

    preview_sql = service._build_transaction_preview_sql(
        "SELECT wt.category_primary, SUM(-wt.amount) AS total_spend "
        "FROM widget_transactions wt "
        "JOIN widget_accounts wa ON wa.id = wt.id "
        "WHERE wt.amount < 0 AND wa.account_type = 'credit' "
        "GROUP BY wt.category_primary "
        "ORDER BY total_spend DESC"
    )

    assert preview_sql == (
        "SELECT date, merchant, amount, category, detailed_category, pending FROM ("
        "SELECT DISTINCT wt.id AS transaction_id, wt.occurred_at AS date, "
        "COALESCE(NULLIF(wt.merchant_name, ''), wt.original_description) AS merchant, "
        "wt.amount AS amount, wt.category_primary AS category, "
        "wt.category_detailed AS detailed_category, wt.pending AS pending "
        "FROM widget_transactions AS wt "
        "JOIN widget_accounts AS wa ON wa.id = wt.id "
        "WHERE wt.amount < 0 AND wa.account_type = 'credit' AND wt.household_id = :_household_id"
        ") AS _transaction_preview "
        "ORDER BY date DESC NULLS LAST, transaction_id DESC NULLS LAST"
    )


def test_transaction_preview_sql_appends_preview_filters():
    service = NamedQueryService(named_query_repo=None)

    preview_sql = service._build_transaction_preview_sql(
        "SELECT wt.id, wt.amount FROM widget_transactions wt WHERE wt.amount < 0",
        TransactionPreviewFilters(
            account_ids=[uuid4()],
            search="coffee",
            start_date="2026-01-01",
            end_date="2026-01-31",
            order_by="amount",
            order_direction="asc",
        ),
    )

    assert (
        "wt.account_id = ANY(:_transaction_preview_account_ids)" in preview_sql
    )
    assert "ILIKE :_transaction_preview_search" in preview_sql
    assert "wt.occurred_at >= :_transaction_preview_start_date" in preview_sql
    assert "wt.occurred_at < :_transaction_preview_end_date_exclusive" in preview_sql
    assert "ORDER BY amount ASC NULLS LAST, transaction_id ASC NULLS LAST" in preview_sql


def test_transaction_preview_filters_validate_date_order():
    service = NamedQueryService(named_query_repo=None)

    with pytest.raises(ValidationError, match="start_date must be on or before end_date"):
        service._normalize_transaction_preview_filters(
            TransactionPreviewFilters(
                start_date="2026-02-01",
                end_date="2026-01-31",
            )
        )


def test_transaction_preview_sql_is_omitted_for_account_only_queries():
    service = NamedQueryService(named_query_repo=None)

    preview_sql = service._build_transaction_preview_sql(
        "SELECT name, current_balance FROM widget_accounts ORDER BY current_balance DESC"
    )

    assert preview_sql is None


def test_generation_returns_valid_candidate_and_consumes_quota():
    usage_repo = FakeUsageRepo()
    service = _generation_service(
        [
            {
                "type": "named_query_candidate",
                "name": "Spending by category",
                "candidate": {
                    "sql_query": (
                        "SELECT category_primary, SUM(amount) AS total "
                        "FROM widget_transactions "
                        "GROUP BY category_primary"
                    ),
                    "chart_type": "bar",
                },
            }
        ],
        usage_repo=usage_repo,
    )

    response = service.generate(db=None, household_id=uuid4(), messages=_message())

    assert response.type == "named_query_candidate"
    assert response.candidate.chart_type == "bar"
    assert usage_repo.usage.quota_units_used == 1
    assert usage_repo.usage.llm_calls == 1


def test_generation_prompt_asks_for_separate_stored_query_name():
    service = _generation_service(
        [
            {
                "type": "named_query_candidate",
                "name": "Grocery Spending by Month",
                "candidate": {
                    "sql_query": (
                        "SELECT category_primary, SUM(amount) AS total "
                        "FROM widget_transactions "
                        "GROUP BY category_primary"
                    ),
                    "chart_type": "bar",
                },
            }
        ],
    )

    service.generate(db=None, household_id=uuid4(), messages=_message())

    system_message = service.llm_client.calls[0][0].content
    assert "top-level name field" in system_message
    assert "candidate object is only the SQL" in system_message
    assert "Grocery Spending by Month" in system_message
    assert "Ask at most 3 more clarifying questions" in system_message
    assert "aggregate `-amount` so totals, averages, and similar metrics come back" in system_message
    assert "SELECT category_primary, SUM(-amount) AS total_spend" in system_message


def test_generation_returns_clarifying_question_and_consumes_quota():
    usage_repo = FakeUsageRepo()
    service = _generation_service(
        [{"type": "clarifying_question", "question": "Which category do you mean?"}],
        usage_repo=usage_repo,
    )

    response = service.generate(db=None, household_id=uuid4(), messages=_message())

    assert response.type == "clarifying_question"
    assert usage_repo.usage.quota_units_used == 1
    assert usage_repo.usage.clarifying_questions == 1


def test_generation_allows_multiple_clarifying_questions_until_limit():
    usage_repo = FakeUsageRepo()
    service = _generation_service(
        [{"type": "clarifying_question", "question": "Do you want spending or income?"}],
        usage_repo=usage_repo,
    )

    response = service.generate(
        db=None,
        household_id=uuid4(),
        messages=[
            NamedQueryGenerationMessage(role="member", content="show Amazon by month"),
            NamedQueryGenerationMessage(
                role="assistant",
                content="Do you want only Amazon purchases or broader retail spending?",
            ),
            NamedQueryGenerationMessage(role="member", content="Only Amazon purchases."),
        ],
    )

    assert response.type == "clarifying_question"
    assert response.question == "Do you want spending or income?"
    assert usage_repo.usage.quota_units_used == 1
    assert usage_repo.usage.clarifying_questions == 1
    system_message = service.llm_client.calls[0][0].content
    assert "Ask at most 2 more clarifying questions" in system_message


def test_generation_converts_question_beyond_limit_into_failure():
    usage_repo = FakeUsageRepo()
    service = _generation_service(
        [{"type": "clarifying_question", "question": "Which account should I use?"}],
        usage_repo=usage_repo,
    )

    response = service.generate(
        db=None,
        household_id=uuid4(),
        messages=[
            NamedQueryGenerationMessage(role="member", content="show subscriptions"),
            NamedQueryGenerationMessage(role="assistant", content="Monthly or yearly?"),
            NamedQueryGenerationMessage(role="member", content="Monthly."),
            NamedQueryGenerationMessage(
                role="assistant",
                content="Only charges or charges and refunds?",
            ),
            NamedQueryGenerationMessage(role="member", content="Only charges."),
            NamedQueryGenerationMessage(
                role="assistant",
                content="All accounts or just credit cards?",
            ),
            NamedQueryGenerationMessage(role="member", content="All accounts."),
        ],
    )

    assert response.type == "generation_failure"
    assert "reached the clarification limit" in response.message
    assert usage_repo.usage.clarifying_questions == 0
    assert usage_repo.usage.generation_failures == 1
    system_message = service.llm_client.calls[0][0].content
    assert "Ask at most 0 more clarifying questions" in system_message


def test_generation_returns_explanation_and_consumes_quota():
    usage_repo = FakeUsageRepo()
    service = _generation_service(
        [{"type": "explanation", "message": "This query groups spending by month."}],
        usage_repo=usage_repo,
    )

    response = service.generate(
        db=None,
        household_id=uuid4(),
        messages=_message("Explain this query"),
    )

    assert response.type == "explanation"
    assert response.message == "This query groups spending by month."
    assert usage_repo.usage.quota_units_used == 1
    assert usage_repo.usage.clarifying_questions == 0


def test_generation_repairs_invalid_sql_without_consuming_extra_quota():
    usage_repo = FakeUsageRepo()
    service = _generation_service(
        [
            {
                "type": "named_query_candidate",
                "name": "Bad query",
                "candidate": {
                    "sql_query": "SELECT * FROM transactions",
                    "chart_type": "line",
                },
            },
            {
                "type": "named_query_candidate",
                "name": "Fixed query",
                "candidate": {
                    "sql_query": "SELECT occurred_at, amount FROM widget_transactions",
                    "chart_type": "line",
                },
            },
        ],
        usage_repo=usage_repo,
    )

    response = service.generate(db=None, household_id=uuid4(), messages=_message())

    assert response.type == "named_query_candidate"
    assert response.name == "Fixed query"
    assert usage_repo.usage.quota_units_used == 1
    assert usage_repo.usage.validation_failures == 1
    assert usage_repo.usage.repair_attempts == 1
    assert usage_repo.usage.llm_calls == 2


def test_generation_failure_after_invalid_repairs_does_not_consume_quota():
    usage_repo = FakeUsageRepo()
    service = _generation_service(
        [
            {
                "type": "named_query_candidate",
                "name": "Bad query",
                "candidate": {
                    "sql_query": "SELECT * FROM transactions",
                    "chart_type": "bar",
                },
            }
        ],
        usage_repo=usage_repo,
        repair_attempts=0,
    )

    response = service.generate(db=None, household_id=uuid4(), messages=_message())

    assert response.type == "generation_failure"
    assert usage_repo.usage.quota_units_used == 0
    assert usage_repo.usage.generation_failures == 1


def test_provider_failure_does_not_consume_quota():
    usage_repo = FakeUsageRepo()
    service = _generation_service(
        [LLMProviderError("provider down")],
        usage_repo=usage_repo,
    )

    with pytest.raises(InternalError):
        service.generate(db=None, household_id=uuid4(), messages=_message())

    assert usage_repo.usage.quota_units_used == 0
    assert usage_repo.usage.provider_failures == 1


def test_exhausted_quota_returns_rate_limit_before_llm_call():
    usage = SimpleNamespace(
        quota_units_used=1,
        llm_calls=0,
        clarifying_questions=0,
        validation_failures=0,
        repair_attempts=0,
        generation_failures=0,
        provider_failures=0,
    )
    usage_repo = FakeUsageRepo(usage=usage)
    service = _generation_service(
        [{"type": "clarifying_question", "question": "unused"}],
        usage_repo=usage_repo,
        daily_quota=1,
    )

    with pytest.raises(RateLimitError):
        service.generate(db=None, household_id=uuid4(), messages=_message())

    assert usage_repo.usage.llm_calls == 0
