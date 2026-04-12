from uuid import UUID
from datetime import date, datetime, timedelta

from .repository import PlaidItemRepository
from ...app.membership.repository import MembershipRepository
from ...exceptions import ConflictError, NotFoundError, ValidationError
from ...infrastructure import Session, PlaidClient
from src.infrastructure.plaid.client import (
    PLAID_COUNTRY_CODES,
    PLAID_REDIRECT_URI,
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
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest


class PlaidItemService:
    def __init__(
        self,
        plaid_item_repo: PlaidItemRepository,
        membership_repo: MembershipRepository,
        plaid_client: PlaidClient,
    ):
        self.plaid_item_repo = plaid_item_repo
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

            if Products("statements") in products:
                req["statements"] = LinkTokenCreateRequestStatements(  # type: ignore
                    end_date=date.today(),
                    start_date=date.today() - timedelta(days=30),
                )

            resp = self.plaid_client.link_token_create(req)
            return resp.to_dict()
        except plaid.ApiException as e:
            raise NotFoundError()

    def exchange_public_token(self, plaid_client: PlaidClient, link_public_token: str):
        try:
            req = ItemPublicTokenExchangeRequest(public_token=link_public_token)
            resp = plaid_client.item_public_token_exchange(req)
        except plaid.ApiException as e:
            raise ValidationError()

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
            pass  # Institution info is optional

        return institution_id, institution_name

    def list_household_items(self, db: Session, household_id: UUID):
        return self.plaid_item_repo.list_household_items(
            db=db, household_id=household_id
        )
