from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from dataclasses import dataclass

from src.modules import *
from src.infrastructure import (
    get_db,
    get_firebase_identity,
    get_kms_service,
    get_plaid_client,
    KMSService,
    PlaidClient,
)
from src.modules.plaid_transaction_sync_jobs.repository import SyncJobsRepository
from src.modules.plaid_transaction_sync_jobs.request_service import (
    SyncJobsRequestService,
)
from src.modules.plaid_transaction_sync_jobs.execution_service import (
    SyncJobsExecutionService,
)
from src.workflows.onboarding import OnboardingOrchestrator
from src.modules.plaid_webhooks.items_service import PlaidItemsWebhookService
from src.modules.plaid_webhooks.service import PlaidWebhookService
from src.modules.plaid_webhooks.transactions_service import (
    PlaidTransactionsWebhookService,
)
from src.modules.plaid_webhooks.verifier import PlaidWebhookVerifier


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(
        user_repo=user_repo,
    )


def get_household_repository() -> HouseholdRepository:
    return HouseholdRepository()


def get_membership_repository() -> MembershipRepository:
    return MembershipRepository()


def get_membership_service(
    membership_repo: MembershipRepository = Depends(get_membership_repository),
    household_repo: HouseholdRepository = Depends(get_household_repository),
) -> MembershipService:
    return MembershipService(
        membership_repo=membership_repo,
        household_repo=household_repo,
    )


def get_household_service(
    household_repo: HouseholdRepository = Depends(get_household_repository),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
) -> HouseholdService:
    return HouseholdService(
        household_repo=household_repo, membership_repo=membership_repo
    )


# Requires User already registered
@dataclass
class RequestContext:
    db: Session
    user: User


# Requires User already registered
def get_current_user(
    db: Session = Depends(get_db),
    firebase_identity: dict = Depends(get_firebase_identity),
    user_repo: UserRepository = Depends(get_user_repository),
):
    firebase_uid = firebase_identity.get("uid")

    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = user_repo.get_user_by_firebase_uid(db, firebase_uid)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# Requires User already registered
def get_request_context(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> RequestContext:

    return RequestContext(
        db=db,
        user=user,
    )


def get_plaid_item_repository():
    return PlaidItemRepository()


def get_plaid_item_service(
    plaid_item_repo: PlaidItemRepository = Depends(get_plaid_item_repository),
    membership_repo: MembershipRepository = Depends(get_membership_repository),
    plaid_client: PlaidClient = Depends(get_plaid_client),
) -> PlaidItemService:
    return PlaidItemService(
        plaid_item_repo=plaid_item_repo,
        membership_repo=membership_repo,
        plaid_client=plaid_client,
    )


def get_plaid_account_repository():
    return PlaidAccountRepository()


def get_plaid_account_service(
    plaid_account_repo: PlaidAccountRepository = Depends(get_plaid_account_repository),
) -> PlaidAccountService:
    return PlaidAccountService(plaid_account_repo=plaid_account_repo)


def get_transaction_repository():
    return TransactionRepository()


def get_transaction_service(
    plaid_item_repo: PlaidItemRepository = Depends(get_plaid_item_repository),
    plaid_account_repo: PlaidAccountRepository = Depends(get_plaid_account_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
) -> TransactionService:
    return TransactionService(
        plaid_item_repo=plaid_item_repo,
        plaid_account_repo=plaid_account_repo,
        transaction_repo=transaction_repo,
    )


def get_sync_jobs_repository() -> SyncJobsRepository:
    return SyncJobsRepository()


def get_sync_jobs_request_service(
    plaid_item_repo: PlaidItemRepository = Depends(get_plaid_item_repository),
    sync_jobs_repo: SyncJobsRepository = Depends(get_sync_jobs_repository),
) -> SyncJobsRequestService:
    return SyncJobsRequestService(
        plaid_items_repo=plaid_item_repo,
        sync_jobs_repo=sync_jobs_repo,
    )


def get_sync_jobs_execution_service(
    plaid_item_repo: PlaidItemRepository = Depends(get_plaid_item_repository),
    sync_jobs_repo: SyncJobsRepository = Depends(get_sync_jobs_repository),
) -> SyncJobsExecutionService:
    return SyncJobsExecutionService(
        plaid_items_repo=plaid_item_repo,
        sync_jobs_repo=sync_jobs_repo,
    )


def get_onboarding_orchestrator(
    plaid_item_service: PlaidItemService = Depends(get_plaid_item_service),
    plaid_account_service: PlaidAccountService = Depends(get_plaid_account_service),
    membership_service: MembershipService = Depends(get_membership_service),
    sync_jobs_request_service: SyncJobsRequestService = Depends(
        get_sync_jobs_request_service
    ),
) -> OnboardingOrchestrator:
    return OnboardingOrchestrator(
        plaid_item_service=plaid_item_service,
        plaid_account_service=plaid_account_service,
        membership_service=membership_service,
        sync_jobs_request_service=sync_jobs_request_service,
    )


def get_plaid_webhook_verifier(
    plaid_client: PlaidClient = Depends(get_plaid_client),
) -> PlaidWebhookVerifier:
    return PlaidWebhookVerifier(plaid_client=plaid_client)


def get_plaid_transactions_webhook_service(
    sync_jobs_request_service: SyncJobsRequestService = Depends(
        get_sync_jobs_request_service
    ),
) -> PlaidTransactionsWebhookService:
    return PlaidTransactionsWebhookService(
        sync_jobs_request_service=sync_jobs_request_service
    )


def get_plaid_items_webhook_service(
    plaid_item_repo: PlaidItemRepository = Depends(get_plaid_item_repository),
    plaid_account_repo: PlaidAccountRepository = Depends(get_plaid_account_repository),
    sync_jobs_request_service: SyncJobsRequestService = Depends(
        get_sync_jobs_request_service
    ),
    sync_jobs_repo: SyncJobsRepository = Depends(get_sync_jobs_repository),
) -> PlaidItemsWebhookService:
    return PlaidItemsWebhookService(
        plaid_item_repo=plaid_item_repo,
        plaid_account_repo=plaid_account_repo,
        sync_jobs_request_service=sync_jobs_request_service,
        sync_jobs_repo=sync_jobs_repo,
    )


def get_plaid_webhook_service(
    transactions_webhook_service: PlaidTransactionsWebhookService = Depends(
        get_plaid_transactions_webhook_service
    ),
    items_webhook_service: PlaidItemsWebhookService = Depends(
        get_plaid_items_webhook_service
    ),
) -> PlaidWebhookService:
    return PlaidWebhookService(
        transactions_webhook_service=transactions_webhook_service,
        items_webhook_service=items_webhook_service,
    )
