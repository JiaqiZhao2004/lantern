from datetime import date

from fastapi import APIRouter, Depends, Query

from src.exceptions import NotFoundError
from src.modules.household_membership.repository import MembershipRepository
from src.modules.plaid_transactions.schema import (
    TransactionLedgerFiltersDTO,
    TransactionLedgerResponseDTO,
)
from src.modules.plaid_transactions.service import TransactionLedgerService

from ..dependencies import (
    RequestContext,
    get_membership_repository,
    get_request_context,
    get_transaction_ledger_service,
)

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.get("", response_model=TransactionLedgerResponseDTO)
def list_transactions(
    ctx: RequestContext = Depends(get_request_context),
    service: TransactionLedgerService = Depends(get_transaction_ledger_service),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
    account_ids: str | None = Query(
        default=None,
        description="Comma-separated account IDs to include.",
    ),
    search: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    order_by: str = Query(default="date"),
    order_direction: str = Query(default="desc"),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
):
    membership = membership_repo.get_membership_for_user(db=ctx.db, user_id=ctx.user.id)
    if membership is None:
        raise NotFoundError(detail="Household not found")

    filters = TransactionLedgerFiltersDTO(
        account_ids=_parse_account_ids(account_ids),
        search=search,
        start_date=start_date,
        end_date=end_date,
        order_by=order_by,
        order_direction=order_direction,
        cursor=cursor,
        limit=limit,
    )
    return service.list_for_household(
        db=ctx.db,
        household_id=membership.household_id,
        filters=filters,
    )


def _parse_account_ids(account_ids: str | None) -> list[str]:
    if account_ids is None or account_ids.strip() == "":
        return []
    return [part.strip() for part in account_ids.split(",") if part.strip()]
