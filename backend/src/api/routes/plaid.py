from uuid import UUID
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Form,
    Path,
    Response,
    status,
)
from sqlalchemy.orm import Session

from ..dependencies import (
    get_db,
    get_connection_service,
    InstitutionConnectionService,
    User,
    get_current_user,
    MembershipService,
    get_membership_service,
    AccountService,
    get_account_service,
    get_kms_service,
    get_link_institution_connection_workflow,
    get_plaid_client,
    KMSService,
    PlaidClient,
    SyncJobsRepository,
    get_sync_jobs_repository,
)
from ...exceptions import NotFoundError
from ...workflows.link_institution_connection import LinkInstitutionConnectionWorkflow

from ...modules.institution_connections.schema import (
    CreateLinkTokenResponseDTO,
    GetConnectionsResponseDTO,
    InstitutionConnectionSimpleDTO,
)
from ...modules.accounts.schema import (
    GetAccountsResponseDTO,
    ConnectionWithAccountsDTO,
    AccountSimpleDTO,
    UpdateAccountTrackingRequestDTO,
)

# ---------- Routes ----------
router = APIRouter(prefix="/api/v1/plaid", tags=["plaid"])


@router.post("/create_link_token", response_model=CreateLinkTokenResponseDTO)
def create_link_token(
    connection_service: InstitutionConnectionService = Depends(get_connection_service),
):
    return connection_service.create_link_token()


@router.post("/item", status_code=status.HTTP_201_CREATED)
def add_item(
    link_public_token: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    kms: KMSService = Depends(get_kms_service),
    plaid_client: PlaidClient = Depends(get_plaid_client),
    workflow: LinkInstitutionConnectionWorkflow = Depends(
        get_link_institution_connection_workflow
    ),
):
    try:
        workflow.link_new_connection(
            db=db,
            kms=kms,
            user=user,
            plaid_client=plaid_client,
            link_public_token=link_public_token,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return Response(status_code=status.HTTP_201_CREATED)


@router.get("/items", response_model=GetConnectionsResponseDTO)
def get_household_connections(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
    connection_service: InstitutionConnectionService = Depends(get_connection_service),
):
    membership = membership_service.get_my_membership(db=db, user_id=user.id)
    if not membership:
        raise NotFoundError()
    household_id = membership.household_id

    connections = connection_service.list_household_connections(
        db=db, household_id=household_id
    )

    return GetConnectionsResponseDTO(
        items=[
            InstitutionConnectionSimpleDTO(
                id=c.id,
                institution_name=c.institution_name,
                status=c.status,
                can_revoke=c.user_id == user.id,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in connections
        ]
    )


@router.get("/accounts", response_model=GetAccountsResponseDTO)
def get_household_accounts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
    account_service: AccountService = Depends(get_account_service),
):
    membership = membership_service.get_my_membership(db=db, user_id=user.id)
    if not membership:
        raise NotFoundError()
    household_id = membership.household_id

    household_accounts = account_service.list_household_accounts(
        db=db, household_id=household_id
    )

    connections_by_id: dict[UUID, ConnectionWithAccountsDTO] = {}
    connection_order: list[UUID] = []

    for account in household_accounts:
        if not account.is_active:
            continue

        conn = account.institution_connection
        if conn.id not in connections_by_id:
            connections_by_id[conn.id] = ConnectionWithAccountsDTO(
                connection_id=conn.id,
                institution_name=conn.institution_name,
                status=conn.status,
                accounts=[],
            )
            connection_order.append(conn.id)

        connections_by_id[conn.id].accounts.append(
            AccountSimpleDTO.model_validate(account)
        )

    for conn_id in connection_order:
        connections_by_id[conn_id].accounts.sort(
            key=lambda account: (
                account.display_order is None,
                account.display_order,
                account.name or "",
            )
        )

    return GetAccountsResponseDTO(
        items=[connections_by_id[conn_id] for conn_id in connection_order]
    )


@router.patch("/accounts/{account_id}", response_model=AccountSimpleDTO)
def update_account_tracking(
    account_id: UUID = Path(..., description="Internal app UUID for the account to update."),
    request: UpdateAccountTrackingRequestDTO = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    membership_service: MembershipService = Depends(get_membership_service),
    account_service: AccountService = Depends(get_account_service),
):
    membership = membership_service.get_my_membership(db=db, user_id=user.id)
    if not membership:
        raise NotFoundError()

    try:
        account = account_service.set_query_tracking_enabled(
            db=db,
            household_id=membership.household_id,
            account_id=account_id,
            is_query_tracking_enabled=request.is_query_tracking_enabled,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return AccountSimpleDTO.model_validate(account)


@router.delete("/item/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_item(
    connection_id: UUID = Path(..., description="Internal app UUID for the connection to revoke."),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    kms: KMSService = Depends(get_kms_service),
    connection_service: InstitutionConnectionService = Depends(get_connection_service),
    sync_jobs_repo: SyncJobsRepository = Depends(get_sync_jobs_repository),
):
    try:
        connection_service.revoke_connection(
            db=db,
            kms=kms,
            sync_jobs_repo=sync_jobs_repo,
            user_id=user.id,
            connection_id=connection_id,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return Response(status_code=status.HTTP_204_NO_CONTENT)
