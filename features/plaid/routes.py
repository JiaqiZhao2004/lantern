
import base64
import os
import datetime as dt
import json
import time
from datetime import date, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

import plaid
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.asset_report_create_request import AssetReportCreateRequest
from plaid.model.asset_report_create_request_options import AssetReportCreateRequestOptions
from plaid.model.asset_report_user import AssetReportUser
from plaid.model.asset_report_get_request import AssetReportGetRequest
from plaid.model.asset_report_pdf_get_request import AssetReportPDFGetRequest
from plaid.model.auth_get_request import AuthGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.identity_get_request import IdentityGetRequest
from plaid.model.investments_transactions_get_request_options import InvestmentsTransactionsGetRequestOptions
from plaid.model.investments_transactions_get_request import InvestmentsTransactionsGetRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.statements_list_request import StatementsListRequest
from plaid.model.link_token_create_request_statements import LinkTokenCreateRequestStatements
from plaid.model.statements_download_request import StatementsDownloadRequest
from plaid.api import plaid_api

from utils import pretty_print_response

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
PLAID_PRODUCTS = os.getenv("PLAID_PRODUCTS", "transactions").split(",")
PLAID_COUNTRY_CODES = os.getenv("PLAID_COUNTRY_CODES", "US").split(",")
SIGNAL_RULESET_KEY = os.getenv("SIGNAL_RULESET_KEY", "")


def empty_to_none(field: str) -> Optional[str]:
    value = os.getenv(field)
    if value is None or len(value) == 0:
        return None
    return value


host = plaid.Environment.Sandbox
if PLAID_ENV == "sandbox":
    host = plaid.Environment.Sandbox
if PLAID_ENV == "production":
    host = plaid.Environment.Production

PLAID_REDIRECT_URI = empty_to_none("PLAID_REDIRECT_URI")

configuration = plaid.Configuration(
    host=host,
    api_key={
        "clientId": PLAID_CLIENT_ID,
        "secret": PLAID_SECRET,
        "plaidVersion": "2020-09-14",
    },
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

products = [Products(p) for p in PLAID_PRODUCTS]

# ====== GLOBAL STATE ======
# NOTE: This is demo-only. See gotchas below.
access_token: Optional[str] = None
user_id: Optional[str] = None
item_id: Optional[str] = None


# ---------- utility methods ----------
def format_error(e: plaid.ApiException) -> Dict[str, Any]:
    response = json.loads(e.body)
    return {
        "error": {
            "status_code": e.status,
            "display_message": response.get("error_message"),
            "error_code": response.get("error_code"),
            "error_type": response.get("error_type"),
        }
    }


def poll_with_retries(request_callback, ms: int = 1000, retries_left: int = 20):
    while retries_left > 0:
        try:
            return request_callback()
        except plaid.ApiException as e:
            response = json.loads(e.body)
            if response.get("error_code") != "PRODUCT_NOT_READY":
                raise
            retries_left -= 1
            if retries_left <= 0:
                raise RuntimeError("Ran out of retries while polling") from e
            time.sleep(ms / 1000)


# ---------- Routes (same paths/methods) ----------
router = APIRouter(prefix="/api/v1/plaid", tags=["plaid"])

@router.post("/info")
def info():
    return {
        "item_id": item_id,
        "access_token": access_token,
        "products": PLAID_PRODUCTS,
    }

@router.post("/create_link_token")
def create_link_token():
    global user_token, user_id
    try:
        req = LinkTokenCreateRequest(
            products=products,
            client_name="Plaid Quickstart",
            country_codes=list(map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)),
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=str(time.time())),
        )

        if PLAID_REDIRECT_URI is not None:
            req["redirect_uri"] = PLAID_REDIRECT_URI

        if Products("statements") in products:
            req["statements"] = LinkTokenCreateRequestStatements(
                end_date=date.today(),
                start_date=date.today() - timedelta(days=30),
            )

        resp = client.link_token_create(req)
        return resp.to_dict()
    except plaid.ApiException as e:
        return JSONResponse(status_code=e.status, content=json.loads(e.body))


@router.post("/set_access_token")
def set_access_token(public_token: str = Form(...)):
    """
    Flask used request.form['public_token'].
    FastAPI: use Form(...) so your frontend can keep sending form-encoded.
    """
    global access_token, item_id, transfer_id
    try:
        req = ItemPublicTokenExchangeRequest(public_token=public_token)
        resp = client.item_public_token_exchange(req)
        access_token = resp["access_token"]
        item_id = resp["item_id"]
        return resp.to_dict()
    except plaid.ApiException as e:
        return JSONResponse(status_code=e.status, content=json.loads(e.body))


@router.get("/auth")
def get_auth():
    try:
        req = AuthGetRequest(access_token=access_token)
        resp = client.auth_get(req)
        pretty_print_response(resp.to_dict())
        return resp.to_dict()
    except plaid.ApiException as e:
        return format_error(e)


@router.get("/transactions")
def get_transactions():
    cursor = ""
    added, modified, removed = [], [], []
    has_more = True
    try:
        while has_more:
            req = TransactionsSyncRequest(access_token=access_token, cursor=cursor)
            resp = client.transactions_sync(req).to_dict()
            cursor = resp["next_cursor"]

            if cursor == "":
                time.sleep(2)
                continue

            added.extend(resp["added"])
            modified.extend(resp["modified"])
            removed.extend(resp["removed"])
            has_more = resp["has_more"]
            pretty_print_response(resp)

        latest_transactions = sorted(added, key=lambda t: t["date"])[-8:]
        return {"latest_transactions": latest_transactions}
    except plaid.ApiException as e:
        return format_error(e)


@router.get("/identity")
def get_identity():
    try:
        req = IdentityGetRequest(access_token=access_token)
        resp = client.identity_get(req)
        pretty_print_response(resp.to_dict())
        return {"error": None, "identity": resp.to_dict()["accounts"]}
    except plaid.ApiException as e:
        return format_error(e)


@router.get("/balance")
def get_balance():
    try:
        req = AccountsBalanceGetRequest(access_token=access_token)
        resp = client.accounts_balance_get(req)
        pretty_print_response(resp.to_dict())
        return resp.to_dict()
    except plaid.ApiException as e:
        return format_error(e)


@router.get("/accounts")
def get_accounts():
    try:
        req = AccountsGetRequest(access_token=access_token)
        resp = client.accounts_get(req)
        pretty_print_response(resp.to_dict())
        return resp.to_dict()
    except plaid.ApiException as e:
        return format_error(e)


@router.get("/assets")
def get_assets():
    try:
        req = AssetReportCreateRequest(
            access_tokens=[access_token],
            days_requested=60,
            options=AssetReportCreateRequestOptions(
                webhook="https://www.example.com",
                client_report_id="123",
                user=AssetReportUser(
                    client_user_id="789",
                    first_name="Jane",
                    middle_name="Leah",
                    last_name="Doe",
                    ssn="123-45-6789",
                    phone_number="(555) 123-4567",
                    email="jane.doe@example.com",
                ),
            ),
        )
        resp = client.asset_report_create(req)
        pretty_print_response(resp.to_dict())
        asset_report_token = resp["asset_report_token"]

        get_req = AssetReportGetRequest(asset_report_token=asset_report_token)
        report_resp = poll_with_retries(lambda: client.asset_report_get(get_req))
        asset_report_json = report_resp["report"]

        pdf_req = AssetReportPDFGetRequest(asset_report_token=asset_report_token)
        pdf = client.asset_report_pdf_get(pdf_req)

        return {
            "error": None,
            "json": asset_report_json.to_dict(),
            "pdf": base64.b64encode(pdf.read()).decode("utf-8"),
        }
    except plaid.ApiException as e:
        return format_error(e)


@router.get("/holdings")
def get_holdings():
    try:
        req = InvestmentsHoldingsGetRequest(access_token=access_token)
        resp = client.investments_holdings_get(req)
        pretty_print_response(resp.to_dict())
        return {"error": None, "holdings": resp.to_dict()}
    except plaid.ApiException as e:
        return format_error(e)


@router.get("/investments_transactions")
def get_investments_transactions():
    start_date = (dt.datetime.now() - dt.timedelta(days=30)).date()
    end_date = dt.datetime.now().date()
    try:
        options = InvestmentsTransactionsGetRequestOptions()
        req = InvestmentsTransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date,
            options=options,
        )
        resp = client.investments_transactions_get(req)
        pretty_print_response(resp.to_dict())
        return {"error": None, "investments_transactions": resp.to_dict()}
    except plaid.ApiException as e:
        return format_error(e)


@router.get("/statements")
def statements():
    try:
        req = StatementsListRequest(access_token=access_token)
        resp = client.statements_list(req)
        pretty_print_response(resp.to_dict())
    except plaid.ApiException as e:
        return format_error(e)

    try:
        dl_req = StatementsDownloadRequest(
            access_token=access_token,
            statement_id=resp["accounts"][0]["statements"][0]["statement_id"],
        )
        pdf = client.statements_download(dl_req)
        return {
            "error": None,
            "json": resp.to_dict(),
            "pdf": base64.b64encode(pdf.read()).decode("utf-8"),
        }
    except plaid.ApiException as e:
        return format_error(e)


@router.get("/item")
def item():
    try:
        item_resp = client.item_get(ItemGetRequest(access_token=access_token))
        inst_req = InstitutionsGetByIdRequest(
            institution_id=item_resp["item"]["institution_id"],
            country_codes=list(map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)),
        )
        inst_resp = client.institutions_get_by_id(inst_req)
        pretty_print_response(item_resp.to_dict())
        pretty_print_response(inst_resp.to_dict())
        return {
            "error": None,
            "item": item_resp.to_dict()["item"],
            "institution": inst_resp.to_dict()["institution"],
        }
    except plaid.ApiException as e:
        return format_error(e)


