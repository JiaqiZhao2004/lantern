from datetime import UTC, datetime
from decimal import Decimal
import re
from typing import Any
from uuid import UUID

import sqlalchemy as sa
import sqlglot
import sqlglot.errors
import sqlglot.expressions as exp
from sqlalchemy.orm import Session

from src.exceptions import InternalError, NotFoundError, RateLimitError, ValidationError
from src.infrastructure.llm import LLMClient, LLMMessage, LLMProviderError
from .models import NamedQuery
from .repository import NamedQueryGenerationUsageRepository, NamedQueryRepository
from .schemas import (
    ColumnMeta,
    NamedQueryCandidate,
    NamedQueryCandidateResponse,
    NamedQueryClarifyingQuestionResponse,
    NamedQueryDataResponse,
    NamedQueryGenerateResponse,
    NamedQueryGenerationFailureResponse,
    NamedQueryGenerationMessage,
)
from .sql_validator import validate_named_query_sql

_ROW_CAP = 500
_GENERATION_DAILY_QUOTA = 100
_REPAIR_ATTEMPTS = 2
_ALLOWED_CHART_TYPES = {"bar", "line"}

_GENERATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "clarifying_question",
                "named_query_candidate",
                "generation_failure",
            ],
        },
        "question": {"type": ["string", "null"]},
        "message": {"type": ["string", "null"]},
        "name": {"type": ["string", "null"]},
        "candidate": {
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "sql_query": {"type": "string"},
                "chart_type": {"type": ["string", "null"], "enum": ["bar", "line", None]},
            },
            "required": ["sql_query", "chart_type"],
        },
    },
    "required": ["type", "question", "message", "name", "candidate"],
}

_SYSTEM_PROMPT = """
You generate SQL candidates for Lantern's Named Query feature.
Return only structured JSON matching the requested schema.

For named_query_candidate responses, put the stored Named Query label in the
top-level name field. Names should be short and specific, using Title Case when
natural. Prefer names like "Grocery Spending by Month" over generic labels like
"Query" or "Untitled Named Query". The candidate object is only the SQL
candidate and chart hint.

The SQL must be a single flat PostgreSQL SELECT:
- No CTEs or WITH clauses.
- No subqueries.
- Only use widget_transactions and widget_accounts.
- Do not filter by household_id; the backend injects that filter.

Available columns and types:
widget_transactions:
- id uuid
- household_id uuid
- occurred_at date
- amount numeric
- pending boolean
- merchant_name text
- category_primary text
- category_detailed text
- payment_channel text
- iso_currency_code text
- original_description text
widget_accounts:
- id uuid
- household_id uuid
- name text
- official_name text
- account_type text
- account_subtype text
- current_balance numeric
- available_balance numeric
- iso_currency_code text
- mask text

category taxonomy
category_primary	category_detailed	DESCRIPTION
INCOME	INCOME_DIVIDENDS	Dividends from investment accounts
INCOME	INCOME_INTEREST_EARNED	Income from interest on savings accounts
INCOME	INCOME_RETIREMENT_PENSION	Income from pension payments 
INCOME	INCOME_TAX_REFUND	Income from tax refunds
INCOME	INCOME_UNEMPLOYMENT	Income from unemployment benefits, including unemployment insurance and healthcare
INCOME	INCOME_WAGES	Income from salaries, gig-economy work, and tips earned
INCOME	INCOME_OTHER_INCOME	Other miscellaneous income, including alimony, social security, child support, and rental
TRANSFER_IN	TRANSFER_IN_CASH_ADVANCES_AND_LOANS	Loans and cash advances deposited into a bank account
TRANSFER_IN	TRANSFER_IN_DEPOSIT	Cash, checks, and ATM deposits into a bank account
TRANSFER_IN	TRANSFER_IN_INVESTMENT_AND_RETIREMENT_FUNDS	Inbound transfers to an investment or retirement account
TRANSFER_IN	TRANSFER_IN_SAVINGS	Inbound transfers to a savings account
TRANSFER_IN	TRANSFER_IN_ACCOUNT_TRANSFER	General inbound transfers from another account
TRANSFER_IN	TRANSFER_IN_OTHER_TRANSFER_IN	Other miscellaneous inbound transactions
TRANSFER_OUT	TRANSFER_OUT_INVESTMENT_AND_RETIREMENT_FUNDS	Transfers to an investment or retirement account, including investment apps such as Acorns, Betterment
TRANSFER_OUT	TRANSFER_OUT_SAVINGS	Outbound transfers to savings accounts
TRANSFER_OUT	TRANSFER_OUT_WITHDRAWAL	Withdrawals from a bank account
TRANSFER_OUT	TRANSFER_OUT_ACCOUNT_TRANSFER	General outbound transfers to another account
TRANSFER_OUT	TRANSFER_OUT_OTHER_TRANSFER_OUT	Other miscellaneous outbound transactions
LOAN_PAYMENTS	LOAN_PAYMENTS_CAR_PAYMENT	Car loans and leases
LOAN_PAYMENTS	LOAN_PAYMENTS_CREDIT_CARD_PAYMENT	Payments to a credit card. These are positive amounts for credit card subtypes and negative for depository subtypes
LOAN_PAYMENTS	LOAN_PAYMENTS_PERSONAL_LOAN_PAYMENT	Personal loans, including cash advances and buy now pay later repayments
LOAN_PAYMENTS	LOAN_PAYMENTS_MORTGAGE_PAYMENT	Payments on mortgages
LOAN_PAYMENTS	LOAN_PAYMENTS_STUDENT_LOAN_PAYMENT	Payments on student loans. For college tuition, refer to "General Services - Education"
LOAN_PAYMENTS	LOAN_PAYMENTS_OTHER_PAYMENT	Other miscellaneous debt payments
BANK_FEES	BANK_FEES_ATM_FEES	Fees incurred for out-of-network ATMs
BANK_FEES	BANK_FEES_FOREIGN_TRANSACTION_FEES	Fees incurred on non-domestic transactions
BANK_FEES	BANK_FEES_INSUFFICIENT_FUNDS	Fees relating to insufficient funds
BANK_FEES	BANK_FEES_INTEREST_CHARGE	Fees incurred for interest on purchases, including not-paid-in-full or interest on cash advances
BANK_FEES	BANK_FEES_OVERDRAFT_FEES	Fees incurred when an account is in overdraft
BANK_FEES	BANK_FEES_OTHER_BANK_FEES	Other miscellaneous bank fees
ENTERTAINMENT	ENTERTAINMENT_CASINOS_AND_GAMBLING	Gambling, casinos, and sports betting
ENTERTAINMENT	ENTERTAINMENT_MUSIC_AND_AUDIO	Digital and in-person music purchases, including music streaming services
ENTERTAINMENT	ENTERTAINMENT_SPORTING_EVENTS_AMUSEMENT_PARKS_AND_MUSEUMS	Purchases made at sporting events, music venues, concerts, museums, and amusement parks
ENTERTAINMENT	ENTERTAINMENT_TV_AND_MOVIES	In home movie streaming services and movie theaters
ENTERTAINMENT	ENTERTAINMENT_VIDEO_GAMES	Digital and in-person video game purchases
ENTERTAINMENT	ENTERTAINMENT_OTHER_ENTERTAINMENT	Other miscellaneous entertainment purchases, including night life and adult entertainment
FOOD_AND_DRINK	FOOD_AND_DRINK_BEER_WINE_AND_LIQUOR	Beer, Wine & Liquor Stores
FOOD_AND_DRINK	FOOD_AND_DRINK_COFFEE	Purchases at coffee shops or cafes
FOOD_AND_DRINK	FOOD_AND_DRINK_FAST_FOOD	Dining expenses for fast food chains
FOOD_AND_DRINK	FOOD_AND_DRINK_GROCERIES	Purchases for fresh produce and groceries, including farmers' markets
FOOD_AND_DRINK	FOOD_AND_DRINK_RESTAURANT	Dining expenses for restaurants, bars, gastropubs, and diners
FOOD_AND_DRINK	FOOD_AND_DRINK_VENDING_MACHINES	Purchases made at vending machine operators
FOOD_AND_DRINK	FOOD_AND_DRINK_OTHER_FOOD_AND_DRINK	Other miscellaneous food and drink, including desserts, juice bars, and delis
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_BOOKSTORES_AND_NEWSSTANDS	Books, magazines, and news 
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_CLOTHING_AND_ACCESSORIES	Apparel, shoes, and jewelry
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_CONVENIENCE_STORES	Purchases at convenience stores
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_DEPARTMENT_STORES	Retail stores with wide ranges of consumer goods, typically specializing in clothing and home goods
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_DISCOUNT_STORES	Stores selling goods at a discounted price
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_ELECTRONICS	Electronics stores and websites
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_GIFTS_AND_NOVELTIES	Photo, gifts, cards, and floral stores
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_OFFICE_SUPPLIES	Stores that specialize in office goods
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_ONLINE_MARKETPLACES	Multi-purpose e-commerce platforms such as Etsy, Ebay and Amazon
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_PET_SUPPLIES	Pet supplies and pet food
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_SPORTING_GOODS	Sporting goods, camping gear, and outdoor equipment
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_SUPERSTORES	Superstores such as Target and Walmart, selling both groceries and general merchandise
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_TOBACCO_AND_VAPE	Purchases for tobacco and vaping products
GENERAL_MERCHANDISE	GENERAL_MERCHANDISE_OTHER_GENERAL_MERCHANDISE	Other miscellaneous merchandise, including toys, hobbies, and arts and crafts
HOME_IMPROVEMENT	HOME_IMPROVEMENT_FURNITURE	Furniture, bedding, and home accessories
HOME_IMPROVEMENT	HOME_IMPROVEMENT_HARDWARE	Building materials, hardware stores, paint, and wallpaper
HOME_IMPROVEMENT	HOME_IMPROVEMENT_REPAIR_AND_MAINTENANCE	Plumbing, lighting, gardening, and roofing
HOME_IMPROVEMENT	HOME_IMPROVEMENT_SECURITY	Home security system purchases
HOME_IMPROVEMENT	HOME_IMPROVEMENT_OTHER_HOME_IMPROVEMENT	Other miscellaneous home purchases, including pool installation and pest control
MEDICAL	MEDICAL_DENTAL_CARE	Dentists and general dental care
MEDICAL	MEDICAL_EYE_CARE	Optometrists, contacts, and glasses stores
MEDICAL	MEDICAL_NURSING_CARE	Nursing care and facilities
MEDICAL	MEDICAL_PHARMACIES_AND_SUPPLEMENTS	Pharmacies and nutrition shops
MEDICAL	MEDICAL_PRIMARY_CARE	Doctors and physicians
MEDICAL	MEDICAL_VETERINARY_SERVICES	Prevention and care procedures for animals
MEDICAL	MEDICAL_OTHER_MEDICAL	Other miscellaneous medical, including blood work, hospitals, and ambulances
PERSONAL_CARE	PERSONAL_CARE_GYMS_AND_FITNESS_CENTERS	Gyms, fitness centers, and workout classes
PERSONAL_CARE	PERSONAL_CARE_HAIR_AND_BEAUTY	Manicures, haircuts, waxing, spa/massages, and bath and beauty products 
PERSONAL_CARE	PERSONAL_CARE_LAUNDRY_AND_DRY_CLEANING	Wash and fold, and dry cleaning expenses
PERSONAL_CARE	PERSONAL_CARE_OTHER_PERSONAL_CARE	Other miscellaneous personal care, including mental health apps and services
GENERAL_SERVICES	GENERAL_SERVICES_ACCOUNTING_AND_FINANCIAL_PLANNING	Financial planning, and tax and accounting services
GENERAL_SERVICES	GENERAL_SERVICES_AUTOMOTIVE	Oil changes, car washes, repairs, and towing
GENERAL_SERVICES	GENERAL_SERVICES_CHILDCARE	Babysitters and daycare
GENERAL_SERVICES	GENERAL_SERVICES_CONSULTING_AND_LEGAL	Consulting and legal services
GENERAL_SERVICES	GENERAL_SERVICES_EDUCATION	Elementary, high school, professional schools, and college tuition
GENERAL_SERVICES	GENERAL_SERVICES_INSURANCE	Insurance for auto, home, and healthcare
GENERAL_SERVICES	GENERAL_SERVICES_POSTAGE_AND_SHIPPING	Mail, packaging, and shipping services
GENERAL_SERVICES	GENERAL_SERVICES_STORAGE	Storage services and facilities
GENERAL_SERVICES	GENERAL_SERVICES_OTHER_GENERAL_SERVICES	Other miscellaneous services, including advertising and cloud storage 
GOVERNMENT_AND_NON_PROFIT	GOVERNMENT_AND_NON_PROFIT_DONATIONS	Charitable, political, and religious donations
GOVERNMENT_AND_NON_PROFIT	GOVERNMENT_AND_NON_PROFIT_GOVERNMENT_DEPARTMENTS_AND_AGENCIES	Government departments and agencies, such as driving licences, and passport renewal
GOVERNMENT_AND_NON_PROFIT	GOVERNMENT_AND_NON_PROFIT_TAX_PAYMENT	Tax payments, including income and property taxes
GOVERNMENT_AND_NON_PROFIT	GOVERNMENT_AND_NON_PROFIT_OTHER_GOVERNMENT_AND_NON_PROFIT	Other miscellaneous government and non-profit agencies
TRANSPORTATION	TRANSPORTATION_BIKES_AND_SCOOTERS	Bike and scooter rentals
TRANSPORTATION	TRANSPORTATION_GAS	Purchases at a gas station
TRANSPORTATION	TRANSPORTATION_PARKING	Parking fees and expenses
TRANSPORTATION	TRANSPORTATION_PUBLIC_TRANSIT	Public transportation, including rail and train, buses, and metro
TRANSPORTATION	TRANSPORTATION_TAXIS_AND_RIDE_SHARES	Taxi and ride share services
TRANSPORTATION	TRANSPORTATION_TOLLS	Toll expenses
TRANSPORTATION	TRANSPORTATION_OTHER_TRANSPORTATION	Other miscellaneous transportation expenses
TRAVEL	TRAVEL_FLIGHTS	Airline expenses
TRAVEL	TRAVEL_LODGING	Hotels, motels, and hosted accommodation such as Airbnb
TRAVEL	TRAVEL_RENTAL_CARS	Rental cars, charter buses, and trucks
TRAVEL	TRAVEL_OTHER_TRAVEL	Other miscellaneous travel expenses
RENT_AND_UTILITIES	RENT_AND_UTILITIES_GAS_AND_ELECTRICITY	Gas and electricity bills
RENT_AND_UTILITIES	RENT_AND_UTILITIES_INTERNET_AND_CABLE	Internet and cable bills
RENT_AND_UTILITIES	RENT_AND_UTILITIES_RENT	Rent payment
RENT_AND_UTILITIES	RENT_AND_UTILITIES_SEWAGE_AND_WASTE_MANAGEMENT	Sewage and garbage disposal bills
RENT_AND_UTILITIES	RENT_AND_UTILITIES_TELEPHONE	Cell phone bills
RENT_AND_UTILITIES	RENT_AND_UTILITIES_WATER	Water bills
RENT_AND_UTILITIES	RENT_AND_UTILITIES_OTHER_UTILITIES	Other miscellaneous utility bills

Amounts use positive values for inflows and negative values for outflows.
For month-by-month requests, default to the current calendar year unless the
Member explicitly asks for a different period.
Allowed chart_type values are "bar", "line", or null.
If the Member's request is ambiguous, ask one clarifying question.
If a request can reasonably map to either a specific merchant or brand filter
or a broader category filter, and those would return meaningfully different
datasets, ask one clarifying question before generating SQL.
When the Member names a specific merchant or brand, consider whether they may
mean only that merchant or the broader category it commonly belongs to.
If both interpretations are plausible, ask instead of guessing.
If the Member asks for anything other than creating Named Query SQL for this app,
return a generation_failure.
If the transcript includes a prior SQL candidate and the Member asks for changes,
revise that candidate instead of starting from scratch.

Valid SQL examples:
- Spending by category this year:
  SELECT category_primary, SUM(amount) AS total_spend
  FROM widget_transactions
  WHERE amount < 0
  GROUP BY category_primary
  ORDER BY total_spend ASC
  LIMIT 10
- Spending by week this year:
  SELECT to_char(occurred_at, 'MM-DD') AS occurred_at_short, SUM(-amount)
  FROM widget_transactions
  WHERE widget_transactions.occurred_at >= date_trunc('year', now())
  GROUP BY occurred_at_short

Clarifying question examples:
- "Uber spending" could mean only Uber merchant transactions or all rideshare /
  transportation spending. Ask: "Do you want only Uber transactions, or all
  rideshare spending?"
- "Amazon spending" could mean only Amazon merchant transactions or broader
  shopping / retail spending. Ask a clarifying question before generating SQL.
""".strip()


class NamedQueryGenerationService:
    def __init__(
        self,
        *,
        llm_client: LLMClient,
        usage_repo: NamedQueryGenerationUsageRepository,
        daily_quota: int = _GENERATION_DAILY_QUOTA,
        repair_attempts: int = _REPAIR_ATTEMPTS,
    ):
        self.llm_client = llm_client
        self.usage_repo = usage_repo
        self.daily_quota = daily_quota
        self.repair_attempts = repair_attempts

    def generate(
        self,
        db: Session,
        household_id: UUID,
        messages: list[NamedQueryGenerationMessage],
    ) -> NamedQueryGenerateResponse:
        usage = self.usage_repo.get_or_create_for_date(
            db=db,
            household_id=household_id,
            usage_date=datetime.now(UTC).date(),
        )
        if usage.quota_units_used >= self.daily_quota:
            raise RateLimitError(detail="Named Query generation quota exhausted for today")

        try:
            raw = self._call_llm(self._initial_llm_messages(messages), db, usage)
        except LLMProviderError as e:
            self.usage_repo.increment(db, usage, provider_failures=1)
            raise InternalError(detail=str(e)) from e

        response = self._coerce_response(raw)
        if response is None:
            self.usage_repo.increment(db, usage, provider_failures=1)
            return self._generation_failure(
                db,
                usage,
                "I could not understand the generated response. Try rephrasing.",
            )

        if response.type == "clarifying_question":
            self.usage_repo.increment(
                db,
                usage,
                quota_units_used=1,
                clarifying_questions=1,
            )
            return response

        if response.type == "generation_failure":
            self.usage_repo.increment(db, usage, generation_failures=1)
            return response

        candidate_response = self._validate_or_repair(
            db=db,
            usage=usage,
            transcript=messages,
            name=response.name,
            candidate=response.candidate,
        )
        if candidate_response.type == "named_query_candidate":
            self.usage_repo.increment(db, usage, quota_units_used=1)
        return candidate_response

    def _call_llm(
        self,
        messages: list[LLMMessage],
        db: Session,
        usage,
    ) -> dict[str, Any]:
        self.usage_repo.increment(db, usage, llm_calls=1)
        return self.llm_client.generate_structured(
            messages=messages,
            schema_name="named_query_generation",
            json_schema=_GENERATION_SCHEMA,
        )

    def _initial_llm_messages(
        self,
        messages: list[NamedQueryGenerationMessage],
    ) -> list[LLMMessage]:
        llm_messages = [LLMMessage(role="system", content=_SYSTEM_PROMPT)]
        for message in messages:
            role = "user" if message.role == "member" else "assistant"
            llm_messages.append(LLMMessage(role=role, content=message.content))
        return llm_messages

    def _repair_llm_messages(
        self,
        transcript: list[NamedQueryGenerationMessage],
        name: str,
        candidate: NamedQueryCandidate,
        validation_error: str,
    ) -> list[LLMMessage]:
        messages = self._initial_llm_messages(transcript)
        messages.append(
            LLMMessage(
                role="assistant",
                content=(
                    "Generated SQL candidate failed validation:\n"
                    f"name: {name}\n"
                    f"chart_type: {candidate.chart_type}\n"
                    f"sql_query:\n{candidate.sql_query}\n"
                    f"validation_error: {validation_error}"
                ),
            )
        )
        messages.append(
            LLMMessage(
                role="user",
                content="Repair the candidate and return valid structured JSON.",
            )
        )
        return messages

    def _validate_or_repair(
        self,
        db: Session,
        usage,
        transcript: list[NamedQueryGenerationMessage],
        name: str,
        candidate: NamedQueryCandidate,
    ) -> NamedQueryGenerateResponse:
        normalized_name = self._normalize_name(name)
        current = self._normalize_candidate(candidate)

        for attempt in range(self.repair_attempts + 1):
            result = validate_named_query_sql(current.sql_query)
            if result.valid:
                return NamedQueryCandidateResponse(
                    name=normalized_name,
                    candidate=current,
                )

            self.usage_repo.increment(db, usage, validation_failures=1)
            if attempt >= self.repair_attempts:
                return self._generation_failure(
                    db,
                    usage,
                    "I could not generate a valid query for that request. Try rephrasing.",
                )

            self.usage_repo.increment(db, usage, repair_attempts=1)
            try:
                repaired_raw = self._call_llm(
                    self._repair_llm_messages(
                        transcript,
                        normalized_name,
                        current,
                        result.error or "Invalid SQL",
                    ),
                    db,
                    usage,
                )
            except LLMProviderError as e:
                self.usage_repo.increment(db, usage, provider_failures=1)
                raise InternalError(detail=str(e)) from e

            repaired = self._coerce_response(repaired_raw)
            if repaired is None:
                self.usage_repo.increment(db, usage, provider_failures=1)
                return self._generation_failure(
                    db,
                    usage,
                    "I could not understand the generated response. Try rephrasing.",
                )
            if repaired.type == "named_query_candidate":
                normalized_name = self._normalize_name(repaired.name)
                current = self._normalize_candidate(repaired.candidate)
            elif repaired.type == "clarifying_question":
                self.usage_repo.increment(db, usage, clarifying_questions=1)
                return repaired
            else:
                self.usage_repo.increment(db, usage, generation_failures=1)
                return repaired

        return self._generation_failure(
            db,
            usage,
            "I could not generate a valid query for that request. Try rephrasing.",
        )

    def _coerce_response(self, raw: dict[str, Any]) -> NamedQueryGenerateResponse | None:
        response_type = raw.get("type")
        if response_type == "clarifying_question":
            question = raw.get("question")
            if isinstance(question, str) and question.strip():
                return NamedQueryClarifyingQuestionResponse(question=question.strip())
            return None

        if response_type == "generation_failure":
            message = raw.get("message")
            if isinstance(message, str) and message.strip():
                return NamedQueryGenerationFailureResponse(message=message.strip())
            return NamedQueryGenerationFailureResponse(
                message="I could not generate a query for that request. Try rephrasing."
            )

        if response_type == "named_query_candidate":
            name = raw.get("name")
            candidate = raw.get("candidate")
            if not isinstance(candidate, dict):
                return None
            sql_query = candidate.get("sql_query")
            chart_type = candidate.get("chart_type")
            if not isinstance(name, str) or not isinstance(sql_query, str):
                return None
            if chart_type is not None and not isinstance(chart_type, str):
                chart_type = None
            return NamedQueryCandidateResponse(
                name=name,
                candidate=NamedQueryCandidate(
                    sql_query=sql_query,
                    chart_type=chart_type,
                )
            )

        return None

    def _normalize_name(self, name: str) -> str:
        return name.strip() or "Untitled Named Query"

    def _normalize_candidate(self, candidate: NamedQueryCandidate) -> NamedQueryCandidate:
        chart_type = candidate.chart_type
        if chart_type not in _ALLOWED_CHART_TYPES:
            chart_type = None
        return NamedQueryCandidate(
            sql_query=candidate.sql_query.strip(),
            chart_type=chart_type,
        )

    def _generation_failure(
        self,
        db: Session,
        usage,
        message: str,
    ) -> NamedQueryGenerationFailureResponse:
        self.usage_repo.increment(db, usage, generation_failures=1)
        return NamedQueryGenerationFailureResponse(message=message)


class NamedQueryService:
    def __init__(self, named_query_repo: NamedQueryRepository):
        self.named_query_repo = named_query_repo

    # ------------------------------------------------------------------
    # Validation helper (shared by preview and create/patch)
    # ------------------------------------------------------------------

    def _validate_sql(self, sql: str) -> list[str]:
        result = validate_named_query_sql(sql)
        if not result.valid:
            raise ValidationError(detail=result.error)
        return result.referenced_columns

    # ------------------------------------------------------------------
    # Preview — execute without saving
    # ------------------------------------------------------------------

    def preview(self, db: Session, household_id: UUID, sql_query: str) -> NamedQueryDataResponse:
        self._validate_sql(sql_query)
        return self._execute(db, household_id, sql_query)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(
        self,
        db: Session,
        household_id: UUID,
        name: str,
        sql_query: str,
        chart_type: str | None,
    ) -> NamedQuery:
        referenced_columns = self._validate_sql(sql_query)
        return self.named_query_repo.create(
            db=db,
            household_id=household_id,
            name=name,
            sql_query=sql_query,
            referenced_columns=referenced_columns,
            chart_type=chart_type,
        )

    def list_for_household(self, db: Session, household_id: UUID) -> list[NamedQuery]:
        return self.named_query_repo.list_by_household(db=db, household_id=household_id)

    def get_data(self, db: Session, household_id: UUID, named_query_id: UUID) -> NamedQueryDataResponse:
        nq = self._get_or_404(db, named_query_id, household_id)
        return self._execute(db, household_id, nq.sql_query)

    def patch(
        self,
        db: Session,
        household_id: UUID,
        named_query_id: UUID,
        name: str | None,
        sql_query: str | None,
        chart_type: str | None,
    ) -> NamedQuery:
        nq = self._get_or_404(db, named_query_id, household_id)

        kwargs: dict = {}
        if name is not None:
            kwargs["name"] = name
        if sql_query is not None:
            kwargs["sql_query"] = sql_query
            kwargs["referenced_columns"] = self._validate_sql(sql_query)
        if chart_type is not None:
            kwargs["chart_type"] = chart_type

        return self.named_query_repo.update(db=db, named_query=nq, **kwargs)

    def delete(self, db: Session, household_id: UUID, named_query_id: UUID) -> None:
        nq = self._get_or_404(db, named_query_id, household_id)
        self.named_query_repo.delete(db=db, named_query=nq)

    # ------------------------------------------------------------------
    # Execution — injects household_id filter, enforces limits
    # ------------------------------------------------------------------

    def _execute(self, db: Session, household_id: UUID, sql_query: str) -> NamedQueryDataResponse:
        # Inject household_id filter and fetch one extra row to detect truncation
        scoped_sql = self._inject_household_filter(sql_query)
        injected = (
            f"SELECT * FROM ({scoped_sql}) AS _nq "
            f"LIMIT {_ROW_CAP + 1}"
        )

        try:
            db.execute(sa.text("SET LOCAL TRANSACTION READ ONLY"))
            db.execute(sa.text("SET LOCAL statement_timeout = '2s'"))
            result = db.execute(
                sa.text(injected),
                {"_household_id": str(household_id)},
            )
        except Exception as e:
            raise ValidationError(detail=self._format_query_execution_error(e)) from e

        result_keys = list(result.keys())
        cursor = getattr(result, "cursor", None)
        cursor_description = getattr(cursor, "description", None)
        raw_rows = result.fetchall()
        truncated = len(raw_rows) > _ROW_CAP
        rows_to_return = raw_rows[:_ROW_CAP]

        columns = [
            ColumnMeta(
                name=col,
                type=str(cursor_description[i].type_code)
                if cursor_description
                else "unknown",
            )
            for i, col in enumerate(result_keys)
        ]

        serialized_rows = []
        for row in rows_to_return:
            record: dict = {}
            for col, val in zip(result_keys, row):
                if isinstance(val, Decimal):
                    record[col] = str(val)
                else:
                    record[col] = val
            serialized_rows.append(record)

        return NamedQueryDataResponse(
            columns=columns,
            rows=serialized_rows,
            truncated=truncated,
        )

    def _inject_household_filter(self, sql_query: str) -> str:
        try:
            stmt = sqlglot.parse_one(sql_query, dialect="postgres")
        except (sqlglot.errors.ParseError, sqlglot.errors.TokenError) as e:
            raise ValidationError(detail=f"SQL parse error: {e}")

        if not isinstance(stmt, exp.Select):
            raise ValidationError(detail="Named Query must be a SELECT statement")

        household_filter: exp.Expression | None = None
        for table in stmt.find_all(exp.Table):
            source_name = table.alias_or_name
            condition = exp.EQ(
                this=exp.column("household_id", table=source_name),
                expression=exp.Placeholder(this="_household_id"),
            )
            household_filter = (
                condition
                if household_filter is None
                else exp.and_(household_filter, condition)
            )

        if household_filter is None:
            raise ValidationError(detail="Named Query must reference at least one table")

        return stmt.where(household_filter, append=True).sql(dialect="postgres")

    def _format_query_execution_error(self, exc: Exception) -> str:
        db_error = getattr(exc, "orig", exc)
        primary = self._db_error_field(db_error, "message_primary")
        hint = self._db_error_field(db_error, "message_hint")

        if primary is None:
            primary = str(db_error).splitlines()[0] if str(db_error) else "SQL error"
            primary = re.sub(r"^\([^)]+\)\s*", "", primary)

        message = f"Query execution failed: {primary}"
        if hint:
            message = f"{message}. {self._simplify_db_hint(hint)}"
        return message

    def _db_error_field(self, exc: Exception, field_name: str) -> str | None:
        diag = getattr(exc, "diag", None)
        value = getattr(diag, field_name, None)
        return str(value) if value else None

    def _simplify_db_hint(self, hint: str) -> str:
        return hint.replace(
            "Perhaps you meant to reference the column ",
            "Perhaps you meant ",
            1,
        )

    def _get_or_404(self, db: Session, named_query_id: UUID, household_id: UUID) -> NamedQuery:
        nq = self.named_query_repo.get_by_id(db=db, named_query_id=named_query_id)
        if nq is None or nq.household_id != household_id:
            raise NotFoundError(detail="Named Query not found")
        return nq
