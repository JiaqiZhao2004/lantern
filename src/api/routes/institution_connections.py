import os
import json
import time
from datetime import date, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload

from ..dependencies import (
    get_db,
    get_plaid_item_service,
    PlaidItemService,
    User,
    get_current_user,
    MembershipService,
    get_membership_service,
    PlaidAccountService,
    get_plaid_account_service,
)
from ...exceptions import NotFoundError

from ...plaid.items.schema import (
    AddItemResponseDTO,
    CreateLinkTokenResponseDTO,
    GetItemsResponseDTO,
    PlaidItemSimpleDTO,
)
from ...plaid.accounts.schema import (
    GetAccountsResponseDTO,
    ItemWithAccountsDTO,
    AccountSimpleDTO,
)

from src.app.user.models import User

# ---------- Routes ----------
router = APIRouter(prefix="/api/v1/plaid", tags=["plaid"])


@router.post("/create_link_token", response_model=CreateLinkTokenResponseDTO)
def create_link_token(
    plaid_item_service: PlaidItemService = Depends(get_plaid_item_service),
):
    return plaid_item_service.create_link_token()


@router.get("/items", response_model=GetItemsResponseDTO)
def get_household_items(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
    plaid_item_service: PlaidItemService = Depends(get_plaid_item_service),
):
    """
    Return all Plaid items belonging to the authenticated user's household.
    TODO: Add pagination (skip / limit) if a user can have many linked items.
    """
    # 1. Resolve the calling user
    membership = membership_service.get_my_membership(db=db, user_id=user.id)
    if not membership:
        raise NotFoundError()
    household_id = membership.household_id

    # 2. Fetch all PlaidItems for this household
    household_items = plaid_item_service.list_household_items(
        db=db, household_id=household_id
    )

    # 3. Serialise via DTO
    return GetItemsResponseDTO(
        items=[
            PlaidItemSimpleDTO(
                id=item.id,
                institution_name=item.institution_name,
                status=item.status,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in household_items
        ]
    )


@router.get("/accounts", response_model=GetAccountsResponseDTO)
def get_household_accounts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
    plaid_account_service: PlaidAccountService = Depends(get_plaid_account_service),
):
    """
    Return all accounts for the authenticated user's household, grouped by linked item
    (institution).  Each item carries its institution name so the client
    can render a grouped list without a second request.

    Only active accounts (is_active=True) are returned.  Hidden accounts
    (is_hidden=True) are included so the client can render a 'hidden'
    section — filter them out client-side if not needed.
    """
    # 1. Resolve the calling user
    membership = membership_service.get_my_membership(db=db, user_id=user.id)
    if not membership:
        raise NotFoundError()
    household_id = membership.household_id

    # 2. Fetch all accounts for this household
    household_accounts = plaid_account_service.list_household_accounts(
        db=db, household_id=household_id
    )

    # 3. Serialise, grouping active accounts under their parent item
    items_by_id: dict[UUID, ItemWithAccountsDTO] = {}
    item_order: list[UUID] = []

    for account in household_accounts:
        if not account.is_active:
            continue

        item = account.item
        if item.id not in items_by_id:
            items_by_id[item.id] = ItemWithAccountsDTO(
                item_id=item.id,
                institution_name=item.institution_name,
                status=item.status,
                accounts=[],
            )
            item_order.append(item.id)

        items_by_id[item.id].accounts.append(AccountSimpleDTO.model_validate(account))

    for item_id in item_order:
        items_by_id[item_id].accounts.sort(
            key=lambda account: (
                account.display_order is None,
                account.display_order,
                account.name or "",
            )
        )

    return GetAccountsResponseDTO(
        items=[items_by_id[item_id] for item_id in item_order]
    )
