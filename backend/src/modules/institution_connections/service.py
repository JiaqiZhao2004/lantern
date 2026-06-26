from uuid import UUID
from datetime import date, datetime, timedelta
import logging

from .repository import InstitutionConnectionRepository
from ..sync_jobs.repository import SyncJobsRepository
from ..household_membership.repository import MembershipRepository
from ...exceptions import ConflictError, NotFoundError, ValidationError, InternalError
from ...infrastructure import Session, PlaidClient
from ...infrastructure.aws.kms import KMSService
from src.infrastructure.plaid.client import (
    PLAID_COUNTRY_CODES,
    PLAID_REDIRECT_URI,
    PLAID_WEBHOOK_URL,
    CountryCode,
    Products,
    products,
)


import plaid
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_create_request_statements import (
    LinkTokenCreateRequestStatements,
)
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.item_remove_request import ItemRemoveRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest


logger = logging.getLogger(__name__)


class InstitutionConnectionService:
    def __init__(
        self,
        connection_repo: InstitutionConnectionRepository,
        membership_repo: MembershipRepository,
        plaid_client: PlaidClient,
    ):
        self.connection_repo = connection_repo
        self.membership_repo = membership_repo
        self.plaid_client = plaid_client

    def create_link_token(self):
        try:
            req = LinkTokenCreateRequest(
                products=products,
                client_name="Plaid Quickstart",
                country_codes=list(map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)),
                language="en",
                user=LinkTokenCreateRequestUser(client_user_id=str(datetime.now())),
            )

            if PLAID_REDIRECT_URI is not None:
                req["redirect_uri"] = PLAID_REDIRECT_URI  # type: ignore

            if PLAID_WEBHOOK_URL:
                req["webhook"] = PLAID_WEBHOOK_URL  # type: ignore

            if Products("statements") in products:
                req["statements"] = LinkTokenCreateRequestStatements(  # type: ignore
                    end_date=date.today(),
                    start_date=date.today() - timedelta(days=30),
                )

            resp = self.plaid_client.link_token_create(req)
            return resp.to_dict()
        except plaid.ApiException as e:
            logger.exception("Failed to create Plaid link token")
            raise InternalError() from e

    def exchange_public_token(self, plaid_client: PlaidClient, link_public_token: str):
        try:
            req = ItemPublicTokenExchangeRequest(public_token=link_public_token)
            resp = plaid_client.item_public_token_exchange(req)
        except plaid.ApiException as e:
            logger.exception("Failed to exchange Plaid public token")
            raise InternalError() from e

        plaid_access_token: str = resp["access_token"]
        plaid_item_id: str = resp["item_id"]
        return plaid_item_id, plaid_access_token

    def get_institution_info(self, plaid_client: PlaidClient, plaid_access_token: str):
        institution_id = None
        institution_name = None
        try:
            item_resp = plaid_client.item_get(
                ItemGetRequest(access_token=plaid_access_token)
            )
            institution_id = item_resp.get("item", {}).get("institution_id")
            if institution_id:
                inst_resp = plaid_client.institutions_get_by_id(
                    InstitutionsGetByIdRequest(
                        institution_id=institution_id,
                        country_codes=list(
                            map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)
                        ),
                    )
                )
                institution_name = inst_resp.get("institution", {}).get("name")
        except Exception:
            logger.warning("Failed to fetch Plaid institution info", exc_info=True)
            pass  # Institution info is optional

        return institution_id, institution_name

    def list_household_connections(self, db: Session, household_id: UUID):
        return self.connection_repo.list_household_connections(
            db=db, household_id=household_id
        )

    def revoke_connection(
        self,
        db: Session,
        kms: KMSService,
        sync_jobs_repo: SyncJobsRepository,
        user_id: UUID,
        connection_id: UUID,
    ):
        connection = self.connection_repo.get_by_id_for_user(
            db=db, connection_id=connection_id, user_id=user_id
        )
        if connection is None:
            raise NotFoundError(detail="Institution connection not found")

        plaid_access_token = kms.decrypt_secret(
            encrypted_data_key=connection.plaid_access_token_encrypted_data_key,
            nonce=connection.plaid_access_token_nonce,
            ciphertext=connection.plaid_access_token_ciphertext,
        )

        try:
            self.plaid_client.item_remove(
                ItemRemoveRequest(access_token=plaid_access_token)
            )
        except plaid.ApiException as e:
            logger.exception(
                "Failed to revoke institution connection",
                extra={"connection_id": str(connection.id)},
            )
            raise InternalError(detail="Unable to revoke institution connection") from e

        sync_jobs_repo.cancel_queued_or_running_for_connection(
            db=db,
            institution_connection_id=connection.id,
            last_error="User revoked institution connection",
        )
        self.connection_repo.delete(db=db, connection=connection)
