import pytest

from src.exceptions import ValidationError
from src.modules.named_queries.service import NamedQueryService
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
