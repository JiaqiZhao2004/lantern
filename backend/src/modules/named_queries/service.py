from decimal import Decimal
import re
from uuid import UUID

import sqlalchemy as sa
import sqlglot
import sqlglot.errors
import sqlglot.expressions as exp
from sqlalchemy.orm import Session

from src.exceptions import NotFoundError, ValidationError
from .models import NamedQuery
from .repository import NamedQueryRepository
from .schemas import NamedQueryDataResponse, ColumnMeta
from .sql_validator import validate_named_query_sql

_ROW_CAP = 500


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
