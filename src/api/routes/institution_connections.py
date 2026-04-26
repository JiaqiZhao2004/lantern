from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    Form,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.orm import Session

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
    get_kms_service,
    get_onboarding_orchestrator,
    get_plaid_client,
    get_plaid_webhook_service,
    get_plaid_webhook_verifier,
    KMSService,
    PlaidClient,
)
from ...exceptions import NotFoundError
from ...plaid.webhooks import (
    PlaidWebhookPayload,
    PlaidWebhookService,
    PlaidWebhookVerificationError,
    PlaidWebhookVerifier,
)
from ...plaid.onboarding.orchestrator import OnboardingOrchestrator

from ...plaid.items.schema import (
    CreateLinkTokenResponseDTO,
    GetItemsResponseDTO,
    PlaidItemSimpleDTO,
)
from ...plaid.accounts.schema import (
    GetAccountsResponseDTO,
    ItemWithAccountsDTO,
    AccountSimpleDTO,
)

# ---------- Routes ----------
router = APIRouter(prefix="/api/v1/plaid", tags=["plaid"])


@router.post("/create_link_token", response_model=CreateLinkTokenResponseDTO)
def create_link_token(
    plaid_item_service: PlaidItemService = Depends(get_plaid_item_service),
):
    return plaid_item_service.create_link_token()


@router.post("/item", status_code=status.HTTP_201_CREATED)
def add_item(
    link_public_token: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    kms: KMSService = Depends(get_kms_service),
    plaid_client: PlaidClient = Depends(get_plaid_client),
    onboarding_orchestrator: OnboardingOrchestrator = Depends(
        get_onboarding_orchestrator
    ),
):
    item = onboarding_orchestrator.onboard_new_item(
        db=db,
        kms=kms,
        user=user,
        plaid_client=plaid_client,
        link_public_token=link_public_token,
    )
    return Response(status_code=status.HTTP_201_CREATED)


@router.post("/webhooks", status_code=status.HTTP_202_ACCEPTED)
async def receive_plaid_webhook(
    request: Request,
    plaid_verification: str | None = Header(default=None, alias="Plaid-Verification"),
    db: Session = Depends(get_db),
    webhook_verifier: PlaidWebhookVerifier = Depends(get_plaid_webhook_verifier),
    webhook_service: PlaidWebhookService = Depends(get_plaid_webhook_service),
):
    raw_body = await request.body()

    try:
        webhook_verifier.verify(
            raw_body=raw_body,
            plaid_verification=plaid_verification,
        )
    except PlaidWebhookVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    try:
        payload = PlaidWebhookPayload.model_validate_json(raw_body)
    except PydanticValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        )

    webhook_service.dispatch(db=db, payload=payload)
    return Response(status_code=status.HTTP_202_ACCEPTED)


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
