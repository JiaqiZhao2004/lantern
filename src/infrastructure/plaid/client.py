# features/plaid/plaid_client.py
# Shared Plaid API client initialisation — imported by both routes.py and
# internal_routes.py to avoid circular imports.

import os
from typing import Optional
from functools import lru_cache

import plaid
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.api import plaid_api

# Re-exported so routes don't need to import from plaid.model directly
__all__ = [
    "CountryCode",
    "Products",
    "client",
    "products",
    "PLAID_COUNTRY_CODES",
    "PLAID_REDIRECT_URI",
    "SIGNAL_RULESET_KEY",
]

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


@lru_cache
def get_plaid_client():
    return client
