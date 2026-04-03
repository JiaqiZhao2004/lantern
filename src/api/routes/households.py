# src/api/routes/households.py
from uuid import UUID

from fastapi import APIRouter, Depends

from ..dependencies import (
    RequestContext,
    get_household_service,
    get_membership_service,
    get_request_context,
)
from src.app import (
    CreateHouseholdRequest,
    HouseholdResponse,
    HouseholdService,
    MembershipResponse,
    MembershipService,
)

router = APIRouter(prefix="/api/v1/households", tags=["households"])


@router.post("/create", response_model=HouseholdResponse)
def create_household(
    request: CreateHouseholdRequest,
    ctx: RequestContext = Depends(get_request_context),
    household_service: HouseholdService = Depends(get_household_service),
):
    household = household_service.create_household(
        db=ctx.db,
        user_id=ctx.user.id,
        household_name=request.name,
    )
    return household


@router.post("/{household_id}/join", response_model=MembershipResponse)
def join_household(
    household_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    membership_service: MembershipService = Depends(get_membership_service),
):
    membership = membership_service.join_household(
        db=ctx.db,
        user_id=ctx.user.id,
        household_id=household_id,
    )
    return membership
