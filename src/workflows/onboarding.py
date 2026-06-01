from plaid.api.plaid_api import PlaidApi
from src.infrastructure import Session, KMSService
from src.modules.user.models import User
from src.modules.household_membership.service import MembershipService
from src.modules.plaid_items.service import PlaidItemService
from src.modules.plaid_accounts.service import PlaidAccountService
from src.modules.plaid_transaction_sync_jobs.request_service import SyncJobsRequestService
from src.exceptions import ConflictError, NotFoundError, ValidationError


class OnboardingOrchestrator:

    def __init__(
        self,
        plaid_item_service: PlaidItemService,
        plaid_account_service: PlaidAccountService,
        membership_service: MembershipService,
        sync_jobs_request_service: SyncJobsRequestService,
    ) -> None:
        self.plaid_item_service = plaid_item_service
        self.plaid_account_service = plaid_account_service
        self.membership_service = membership_service
        self.sync_jobs_request_service = sync_jobs_request_service

    def onboard_new_item(
        self,
        db: Session,
        kms: KMSService,
        user: User,
        plaid_client: PlaidApi,
        link_public_token: str,
    ):
        # 1. Exchange public token with Plaid
        plaid_item_id, plaid_access_token = (
            self.plaid_item_service.exchange_public_token(
                plaid_client=plaid_client, link_public_token=link_public_token
            )
        )

        # 2. Get institution_id and institution_name
        institution_id, institution_name = self.plaid_item_service.get_institution_info(
            plaid_client=plaid_client, plaid_access_token=plaid_access_token
        )

        # 3. Gather user data
        membership = self.membership_service.get_my_membership(db=db, user_id=user.id)
        if membership is None:
            raise NotFoundError()
        household_id = membership.household_id

        # 4. Persist the PlaidItem
        item = self.plaid_item_service.plaid_item_repo.create_encrypted(
            db=db,
            kms=kms,
            user=user,
            household_id=household_id,
            plaid_item_id=plaid_item_id,
            plaid_access_token=plaid_access_token,
            institution_id=institution_id,
            institution_name=institution_name,
        )

        # 5. Fetch accounts
        self.plaid_account_service.sync_accounts_for_item(
            plaid_client=plaid_client, item=item, db=db, kms=kms
        )

        # 6. Create first sync job
        self.sync_jobs_request_service.create_onboarding_sync_job(
            db=db, plaid_item=item
        )

        return item
