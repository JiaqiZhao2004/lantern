import uuid
from uuid import UUID

from sqlalchemy.orm import Session

from .models import NamedQuery

_UNSET = object()


class NamedQueryRepository:
    def get_by_id(self, db: Session, named_query_id: UUID) -> NamedQuery | None:
        return db.query(NamedQuery).filter_by(id=named_query_id).first()

    def list_by_household(self, db: Session, household_id: UUID) -> list[NamedQuery]:
        return (
            db.query(NamedQuery)
            .filter_by(household_id=household_id)
            .order_by(NamedQuery.created_at)
            .all()
        )

    def create(
        self,
        db: Session,
        household_id: UUID,
        name: str,
        sql_query: str,
        referenced_columns: list[str] | None,
        chart_type: str | None,
    ) -> NamedQuery:
        nq = NamedQuery(
            household_id=household_id,
            name=name,
            sql_query=sql_query,
            referenced_columns=referenced_columns,
            chart_type=chart_type,
        )
        db.add(nq)
        db.flush()
        return nq

    def update(
        self,
        db: Session,
        named_query: NamedQuery,
        name: str | object = _UNSET,
        sql_query: str | object = _UNSET,
        referenced_columns: list[str] | None | object = _UNSET,
        chart_type: str | None | object = _UNSET,
    ) -> NamedQuery:
        fields = dict(
            name=name,
            sql_query=sql_query,
            referenced_columns=referenced_columns,
            chart_type=chart_type,
        )
        for key, value in fields.items():
            if value is not _UNSET:
                setattr(named_query, key, value)
        db.flush()
        return named_query

    def delete(self, db: Session, named_query: NamedQuery) -> None:
        db.delete(named_query)
        db.flush()
