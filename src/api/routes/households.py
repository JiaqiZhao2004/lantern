# src/api/routes/households.py
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

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
    try:
        household = household_service.create_household(
            db=ctx.db,
            user_id=ctx.user.id,
            household_name=request.name,
        )
        ctx.db.commit()
        ctx.db.refresh(household)
    except Exception:
        ctx.db.rollback()
        raise

    return household


@router.get("/me/household", response_model=HouseholdResponse)
def get_my_household(
    ctx: RequestContext = Depends(get_request_context),
    household_service: HouseholdService = Depends(get_household_service),
):
    household = household_service.get_my_household(
        db=ctx.db,
        user_id=ctx.user.id,
    )
    return household


@router.get("/me/membership", response_model=MembershipResponse)
def get_my_membership(
    ctx: RequestContext = Depends(get_request_context),
    membership_service: MembershipService = Depends(get_membership_service),
):
    membership = membership_service.get_my_membership(
        db=ctx.db,
        user_id=ctx.user.id,
    )
    return membership


@router.post("/{household_id}/join", response_model=MembershipResponse)
def join_household(
    household_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    membership_service: MembershipService = Depends(get_membership_service),
):
    try:
        membership = membership_service.join_household(
            db=ctx.db,
            user_id=ctx.user.id,
            household_id=household_id,
        )
        ctx.db.commit()
        ctx.db.refresh(membership)
    except Exception:
        ctx.db.rollback()
        raise

    return membership


@router.get("/{household_id}/members", response_model=list[MembershipResponse])
def get_household_members(
    household_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    membership_service: MembershipService = Depends(get_membership_service),
):
    memberships = membership_service.list_household_members(
        db=ctx.db,
        requester_user_id=ctx.user.id,
        household_id=household_id,
    )
    return memberships


@router.delete("/{household_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_household(
    household_id: UUID,
    ctx: RequestContext = Depends(get_request_context),
    membership_service: MembershipService = Depends(get_membership_service),
):
    try:
        membership_service.leave_household(
            db=ctx.db,
            user_id=ctx.user.id,
            household_id=household_id,
        )
        ctx.db.commit()
    except Exception:
        ctx.db.rollback()
        raise

    return Response(status_code=status.HTTP_204_NO_CONTENT)
