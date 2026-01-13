# server_fastapi.py
import base64
import os
import datetime as dt
import json
import time
from datetime import date, timedelta
import uuid
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import plaid
from plaid.model.payment_amount import PaymentAmount
from plaid.model.payment_amount_currency import PaymentAmountCurrency
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.recipient_bacs_nullable import RecipientBACSNullable
from plaid.model.payment_initiation_address import PaymentInitiationAddress
from plaid.model.payment_initiation_recipient_create_request import PaymentInitiationRecipientCreateRequest
from plaid.model.payment_initiation_payment_create_request import PaymentInitiationPaymentCreateRequest
from plaid.model.payment_initiation_payment_get_request import PaymentInitiationPaymentGetRequest
from plaid.model.link_token_create_request_payment_initiation import LinkTokenCreateRequestPaymentInitiation
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.user_create_request import UserCreateRequest
from plaid.model.consumer_report_user_identity import ConsumerReportUserIdentity
from plaid.model.client_user_identity import ClientUserIdentity
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
from plaid.model.transfer_authorization_create_request import TransferAuthorizationCreateRequest
from plaid.model.transfer_create_request import TransferCreateRequest
from plaid.model.transfer_get_request import TransferGetRequest
from plaid.model.transfer_network import TransferNetwork
from plaid.model.transfer_type import TransferType
from plaid.model.transfer_authorization_user_in_request import TransferAuthorizationUserInRequest
from plaid.model.ach_class import ACHClass
from plaid.model.transfer_create_idempotency_key import TransferCreateIdempotencyKey
from plaid.model.transfer_user_address_in_request import TransferUserAddressInRequest
from plaid.model.signal_evaluate_request import SignalEvaluateRequest
from plaid.model.statements_list_request import StatementsListRequest
from plaid.model.link_token_create_request_statements import LinkTokenCreateRequestStatements
from plaid.model.link_token_create_request_cra_options import LinkTokenCreateRequestCraOptions
from plaid.model.statements_download_request import StatementsDownloadRequest
from plaid.model.consumer_report_permissible_purpose import ConsumerReportPermissiblePurpose
from plaid.model.cra_check_report_base_report_get_request import CraCheckReportBaseReportGetRequest
from plaid.model.cra_check_report_pdf_get_request import CraCheckReportPDFGetRequest
from plaid.model.cra_check_report_income_insights_get_request import CraCheckReportIncomeInsightsGetRequest
from plaid.model.cra_check_report_partner_insights_get_request import CraCheckReportPartnerInsightsGetRequest
from plaid.model.cra_pdf_add_ons import CraPDFAddOns
from plaid.api import plaid_api

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# ====== GLOBAL STATE (same as your Flask demo) ======
# NOTE: This is demo-only. See gotchas below.
access_token: Optional[str] = None
payment_id: Optional[str] = None
transfer_id: Optional[str] = None
user_token: Optional[str] = None
user_id: Optional[str] = None
item_id: Optional[str] = None

authorization_id: Optional[str] = None
account_id: Optional[str] = None
# ====================================================


def pretty_print_response(response: Any) -> None:
    print(json.dumps(response, indent=2, sort_keys=True, default=str))


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

@app.post("/api/info")
def info():
    return {
        "item_id": item_id,
        "access_token": access_token,
        "products": PLAID_PRODUCTS,
    }


@app.post("/api/create_link_token_for_payment")
def create_link_token_for_payment():
    global payment_id
    try:
        req = PaymentInitiationRecipientCreateRequest(
            name="John Doe",
            bacs=RecipientBACSNullable(account="26207729", sort_code="560029"),
            address=PaymentInitiationAddress(
                street=["street name 999"],
                city="city",
                postal_code="99999",
                country="GB",
            ),
        )
        resp = client.payment_initiation_recipient_create(req)
        recipient_id = resp["recipient_id"]

        req = PaymentInitiationPaymentCreateRequest(
            recipient_id=recipient_id,
            reference="TestPayment",
            amount=PaymentAmount(PaymentAmountCurrency("GBP"), value=100.00),
        )
        resp = client.payment_initiation_payment_create(req)
        pretty_print_response(resp.to_dict())

        payment_id = resp["payment_id"]

        link_req = LinkTokenCreateRequest(
            products=[Products("payment_initiation")],
            client_name="Plaid Test",
            country_codes=list(map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)),
            language="en",
            user=LinkTokenCreateRequestUser(client_user_id=str(time.time())),
            payment_initiation=LinkTokenCreateRequestPaymentInitiation(payment_id=payment_id),
        )
        if PLAID_REDIRECT_URI is not None:
            link_req["redirect_uri"] = PLAID_REDIRECT_URI

        link_resp = client.link_token_create(link_req)
        pretty_print_response(link_resp.to_dict())
        return link_resp.to_dict()
    except plaid.ApiException as e:
        return JSONResponse(status_code=e.status, content=json.loads(e.body))


@app.post("/api/create_link_token")
def create_link_token():
    global user_token, user_id
    try:
        cra_products = {"cra_base_report", "cra_income_insights", "cra_partner_insights"}
        is_cra = any(p in cra_products for p in PLAID_PRODUCTS)

        if is_cra and user_id and not user_token:
            req = LinkTokenCreateRequest(
                products=products,
                client_name="Plaid Quickstart",
                country_codes=list(map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES)),
                language="en",
            )
        else:
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

        if is_cra:
            if user_token:
                req["user_token"] = user_token
            elif user_id:
                req["user_id"] = user_id
            req["consumer_report_permissible_purpose"] = ConsumerReportPermissiblePurpose(
                "ACCOUNT_REVIEW_CREDIT"
            )
            req["cra_options"] = LinkTokenCreateRequestCraOptions(days_requested=60)

        resp = client.link_token_create(req)
        return resp.to_dict()
    except plaid.ApiException as e:
        return JSONResponse(status_code=e.status, content=json.loads(e.body))


@app.post("/api/create_user_token")
def create_user_token():
    global user_token, user_id
    client_user_id = "user_" + str(uuid.uuid4())

    cra_products = {"cra_base_report", "cra_income_insights", "cra_partner_insights"}
    try:
        user_create_req = UserCreateRequest(client_user_id=client_user_id)

        if any(p in cra_products for p in PLAID_PRODUCTS):
            identity = ClientUserIdentity(
                name={"given_name": "Harry", "family_name": "Potter"},
                date_of_birth=date(1980, 7, 31),
                phone_numbers=[{"data": "+16174567890", "primary": True}],
                emails=[{"data": "harrypotter@example.com", "primary": True}],
                addresses=[
                    {
                        "street_1": "4 Privet Drive",
                        "city": "New York",
                        "region": "NY",
                        "postal_code": "11111",
                        "country": "US",
                        "primary": True,
                    }
                ],
            )
            user_create_req["identity"] = identity

        user_resp = client.user_create(user_create_req)
        if "user_token" in user_resp:
            user_token = user_resp["user_token"]
        if "user_id" in user_resp:
            user_id = user_resp["user_id"]
        return user_resp.to_dict()

    except plaid.ApiException as e:
        error_body = json.loads(e.body)
        if error_body.get("error_code") == "INVALID_FIELD" and any(
            p in cra_products for p in PLAID_PRODUCTS
        ):
            try:
                retry_req = UserCreateRequest(client_user_id=client_user_id)
                consumer_identity = ConsumerReportUserIdentity(
                    first_name="Harry",
                    last_name="Potter",
                    date_of_birth=date(1980, 7, 31),
                    phone_numbers=["+16174567890"],
                    emails=["harrypotter@example.com"],
                    primary_address={
                        "city": "New York",
                        "region": "NY",
                        "street": "4 Privet Drive",
                        "postal_code": "11111",
                        "country": "US",
                    },
                )
                retry_req["consumer_report_user_identity"] = consumer_identity
                user_resp = client.user_create(retry_req)
                if "user_token" in user_resp:
                    user_token = user_resp["user_token"]
                if "user_id" in user_resp:
                    user_id = user_resp["user_id"]
                return user_resp.to_dict()
            except plaid.ApiException as retry_e:
                return JSONResponse(status_code=retry_e.status, content=json.loads(retry_e.body))

        return JSONResponse(status_code=e.status, content=json.loads(e.body))


@app.post("/api/set_access_token")
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


@app.get("/api/auth")
def get_auth():
    try:
        req = AuthGetRequest(access_token=access_token)
        resp = client.auth_get(req)
        pretty_print_response(resp.to_dict())
        return resp.to_dict()
    except plaid.ApiException as e:
        return format_error(e)


@app.get("/api/transactions")
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


@app.get("/api/identity")
def get_identity():
    try:
        req = IdentityGetRequest(access_token=access_token)
        resp = client.identity_get(req)
        pretty_print_response(resp.to_dict())
        return {"error": None, "identity": resp.to_dict()["accounts"]}
    except plaid.ApiException as e:
        return format_error(e)


@app.get("/api/balance")
def get_balance():
    try:
        req = AccountsBalanceGetRequest(access_token=access_token)
        resp = client.accounts_balance_get(req)
        pretty_print_response(resp.to_dict())
        return resp.to_dict()
    except plaid.ApiException as e:
        return format_error(e)


@app.get("/api/accounts")
def get_accounts():
    try:
        req = AccountsGetRequest(access_token=access_token)
        resp = client.accounts_get(req)
        pretty_print_response(resp.to_dict())
        return resp.to_dict()
    except plaid.ApiException as e:
        return format_error(e)


@app.get("/api/assets")
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


@app.get("/api/holdings")
def get_holdings():
    try:
        req = InvestmentsHoldingsGetRequest(access_token=access_token)
        resp = client.investments_holdings_get(req)
        pretty_print_response(resp.to_dict())
        return {"error": None, "holdings": resp.to_dict()}
    except plaid.ApiException as e:
        return format_error(e)


@app.get("/api/investments_transactions")
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


@app.get("/api/transfer_authorize")
def transfer_authorize():
    global authorization_id, account_id
    try:
        acct_resp = client.accounts_get(AccountsGetRequest(access_token=access_token))
        account_id = acct_resp["accounts"][0]["account_id"]

        req = TransferAuthorizationCreateRequest(
            access_token=access_token,
            account_id=account_id,
            type=TransferType("debit"),
            network=TransferNetwork("ach"),
            amount="1.00",
            ach_class=ACHClass("ppd"),
            user=TransferAuthorizationUserInRequest(
                legal_name="FirstName LastName",
                email_address="foobar@email.com",
                address=TransferUserAddressInRequest(
                    street="123 Main St.",
                    city="San Francisco",
                    region="CA",
                    postal_code="94053",
                    country="US",
                ),
            ),
        )
        resp = client.transfer_authorization_create(req)
        pretty_print_response(resp.to_dict())
        authorization_id = resp["authorization"]["id"]
        return resp.to_dict()
    except plaid.ApiException as e:
        return format_error(e)


@app.get("/api/transfer_create")
def transfer_create():
    try:
        req = TransferCreateRequest(
            access_token=access_token,
            account_id=account_id,
            authorization_id=authorization_id,
            description="Debit",
        )
        resp = client.transfer_create(req)
        pretty_print_response(resp.to_dict())
        return resp.to_dict()
    except plaid.ApiException as e:
        return format_error(e)


@app.get("/api/statements")
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


@app.get("/api/signal_evaluate")
def signal_evaluate():
    global account_id
    try:
        acct_resp = client.accounts_get(AccountsGetRequest(access_token=access_token))
        account_id = acct_resp["accounts"][0]["account_id"]

        client_transaction_id = f"txn-{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
        params = {
            "access_token": access_token,
            "account_id": account_id,
            "client_transaction_id": client_transaction_id,
            "amount": 100.00,
        }
        if SIGNAL_RULESET_KEY:
            params["ruleset_key"] = SIGNAL_RULESET_KEY

        req = SignalEvaluateRequest(**params)
        resp = client.signal_evaluate(req)
        pretty_print_response(resp.to_dict())
        return resp.to_dict()
    except plaid.ApiException as e:
        return format_error(e)


@app.get("/api/payment")
def payment():
    global payment_id
    try:
        req = PaymentInitiationPaymentGetRequest(payment_id=payment_id)
        resp = client.payment_initiation_payment_get(req)
        pretty_print_response(resp.to_dict())
        return {"error": None, "payment": resp.to_dict()}
    except plaid.ApiException as e:
        return format_error(e)


@app.get("/api/item")
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


@app.get("/api/cra/get_base_report")
def cra_get_base_report():
    try:
        if user_token:
            base_req = CraCheckReportBaseReportGetRequest(user_token=user_token, item_ids=[])
            pdf_req = CraCheckReportPDFGetRequest(user_token=user_token)
        elif user_id:
            base_req = CraCheckReportBaseReportGetRequest(user_id=user_id, item_ids=[])
            pdf_req = CraCheckReportPDFGetRequest(user_id=user_id)
        else:
            raise HTTPException(status_code=400, detail="Missing user_token/user_id")

        get_resp = poll_with_retries(lambda: client.cra_check_report_base_report_get(base_req))
        pretty_print_response(get_resp.to_dict())

        pdf_resp = client.cra_check_report_pdf_get(pdf_req)

        return {
            "report": get_resp.to_dict()["report"],
            "pdf": base64.b64encode(pdf_resp.read()).decode("utf-8"),
        }
    except plaid.ApiException as e:
        return format_error(e)


@app.get("/api/cra/get_income_insights")
def cra_get_income_insights():
    try:
        if user_token:
            insights_req = CraCheckReportIncomeInsightsGetRequest(user_token=user_token)
            pdf_req = CraCheckReportPDFGetRequest(
                user_token=user_token,
                add_ons=[CraPDFAddOns("cra_income_insights")],
            )
        elif user_id:
            insights_req = CraCheckReportIncomeInsightsGetRequest(user_id=user_id)
            pdf_req = CraCheckReportPDFGetRequest(
                user_id=user_id,
                add_ons=[CraPDFAddOns("cra_income_insights")],
            )
        else:
            raise HTTPException(status_code=400, detail="Missing user_token/user_id")

        get_resp = poll_with_retries(lambda: client.cra_check_report_income_insights_get(insights_req))
        pretty_print_response(get_resp.to_dict())

        pdf_resp = client.cra_check_report_pdf_get(pdf_req)
        return {
            "report": get_resp.to_dict()["report"],
            "pdf": base64.b64encode(pdf_resp.read()).decode("utf-8"),
        }
    except plaid.ApiException as e:
        return format_error(e)


@app.get("/api/cra/get_partner_insights")
def cra_get_partner_insights():
    try:
        if user_token:
            partner_req = CraCheckReportPartnerInsightsGetRequest(user_token=user_token)
        elif user_id:
            partner_req = CraCheckReportPartnerInsightsGetRequest(user_id=user_id)
        else:
            raise HTTPException(status_code=400, detail="Missing user_token/user_id")

        resp = poll_with_retries(lambda: client.cra_check_report_partner_insights_get(partner_req))
        pretty_print_response(resp.to_dict())
        return resp.to_dict()
    except plaid.ApiException as e:
        return format_error(e)
