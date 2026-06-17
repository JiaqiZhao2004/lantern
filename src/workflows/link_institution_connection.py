from plaid.api.plaid_api import PlaidApi
from src.infrastructure import Session, KMSService
from src.modules.user.models import User
from src.modules.household_membership.service import MembershipService
from src.modules.institution_connections.service import InstitutionConnectionService
from src.modules.accounts.service import AccountService
from src.modules.sync_jobs.request_service import SyncJobsRequestService
from src.exceptions import ConflictError, NotFoundError, ValidationError


class LinkInstitutionConnectionWorkflow:

    def __init__(
        self,
        connection_service: InstitutionConnectionService,
        account_service: AccountService,
        membership_service: MembershipService,
        sync_jobs_request_service: SyncJobsRequestService,
    ) -> None:
        self.connection_service = connection_service
        self.account_service = account_service
        self.membership_service = membership_service
        self.sync_jobs_request_service = sync_jobs_request_service

    def link_new_connection(
        self,
        db: Session,
        kms: KMSService,
        user: User,
        plaid_client: PlaidApi,
        link_public_token: str,
    ):
        # 1. Exchange public token with Plaid
        plaid_item_id, plaid_access_token = (
            self.connection_service.exchange_public_token(
                plaid_client=plaid_client, link_public_token=link_public_token
            )
        )

        # 2. Get institution_id and institution_name
        institution_id, institution_name = self.connection_service.get_institution_info(
            plaid_client=plaid_client, plaid_access_token=plaid_access_token
        )

        # 3. Gather user data
        membership = self.membership_service.get_my_membership(db=db, user_id=user.id)
        if membership is None:
            raise NotFoundError()
        household_id = membership.household_id

        # 4. Persist the InstitutionConnection
        connection = self.connection_service.connection_repo.create_encrypted(
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
        self.account_service.sync_accounts_for_connection(
            plaid_client=plaid_client, connection=connection, db=db, kms=kms
        )

        # 6. Create first sync job
        self.sync_jobs_request_service.create_initial_link_sync_job(
            db=db, connection=connection
        )

        return connection
