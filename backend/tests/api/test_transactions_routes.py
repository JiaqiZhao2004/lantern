from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

import src.api.routes.transactions as transaction_routes
from src.server import app


class FakeService:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def list_for_household(self, db, household_id, filters):
        self.calls.append((household_id, filters))
        return self.response


class FakeMembershipRepo:
    def __init__(self, membership):
        self.membership = membership

    def get_membership_for_user(self, db, user_id):
        return self.membership


def _override_request_context():
    return SimpleNamespace(db=object(), user=SimpleNamespace(id=uuid4()))


def test_list_transactions_passes_filters_through_to_service():
    household_id = uuid4()
    account_a = uuid4()
    account_b = uuid4()
    service = FakeService(
        {
            "items": [
                {
                    "id": str(uuid4()),
                    "account_id": str(account_a),
                    "account_name": "Checking",
                    "institution_name": "Chase",
                    "occurred_at": datetime(2026, 6, 1, tzinfo=UTC).isoformat(),
                    "amount": str(Decimal("-12.34")),
                    "merchant_name": "Coffee",
                    "original_description": "COFFEE SHOP",
                    "pending": True,
                    "category_primary": "FOOD_AND_DRINK",
                    "category_detailed": "FOOD_AND_DRINK_COFFEE",
                    "iso_currency_code": "USD",
                }
            ],
            "page": {
                "next_cursor": "next",
                "has_next_page": True,
                "total_count": 12,
                "limit": 50,
            },
        }
    )
    app.dependency_overrides[transaction_routes.get_request_context] = _override_request_context
    app.dependency_overrides[transaction_routes.get_membership_repository] = (
        lambda: FakeMembershipRepo(SimpleNamespace(household_id=household_id))
    )
    app.dependency_overrides[transaction_routes.get_transaction_ledger_service] = (
        lambda: service
    )

    try:
        response = TestClient(app).get(
            "/api/v1/transactions",
            params={
                "account_ids": f"{account_a},{account_b}",
                "search": "coffee",
                "start_date": "2026-06-01",
                "end_date": "2026-06-30",
                "order_by": "amount",
                "order_direction": "asc",
                "cursor": "abc123",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["page"]["total_count"] == 12

    _, filters = service.calls[0]
    assert service.calls[0][0] == household_id
    assert filters.account_ids == [account_a, account_b]
    assert filters.search == "coffee"
    assert str(filters.start_date) == "2026-06-01"
    assert str(filters.end_date) == "2026-06-30"
    assert filters.order_by == "amount"
    assert filters.order_direction == "asc"
    assert filters.cursor == "abc123"
