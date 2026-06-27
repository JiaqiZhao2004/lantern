from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.exceptions import ValidationError
from src.modules.plaid_transactions.schema import TransactionLedgerFiltersDTO
from src.modules.plaid_transactions.service import TransactionLedgerService


class FakeTransactionRepo:
    def __init__(self, total_count, rows):
        self.total_count = total_count
        self.rows = rows

    def list_household_transactions(self, db, **kwargs):
        return self.total_count, self.rows


def test_list_for_household_returns_exact_count_and_next_cursor():
    first_id = uuid4()
    second_id = uuid4()
    repo = FakeTransactionRepo(
        total_count=12,
        rows=[
            SimpleNamespace(
                id=first_id,
                row_num=1,
                account_id=uuid4(),
                account_name="Checking",
                institution_name="Chase",
                occurred_at=datetime(2026, 6, 20, tzinfo=UTC),
                amount=Decimal("-18.22"),
                merchant_name="Coffee",
                original_description="COFFEE SHOP",
                pending=False,
                category_primary="FOOD_AND_DRINK",
                category_detailed="FOOD_AND_DRINK_COFFEE",
                iso_currency_code="USD",
            ),
            SimpleNamespace(
                id=second_id,
                row_num=2,
                account_id=uuid4(),
                account_name="Savings",
                institution_name="Ally",
                occurred_at=datetime(2026, 6, 19, tzinfo=UTC),
                amount=Decimal("1250.00"),
                merchant_name="Payroll",
                original_description="ACH CREDIT PAYROLL",
                pending=True,
                category_primary="INCOME",
                category_detailed="INCOME_WAGES",
                iso_currency_code="USD",
            ),
        ],
    )
    service = TransactionLedgerService(transaction_repo=repo)

    result = service.list_for_household(
        db=None,
        household_id=uuid4(),
        filters=TransactionLedgerFiltersDTO(limit=1),
    )

    assert result.page.total_count == 12
    assert result.page.has_next_page is True
    assert result.page.next_cursor is not None
    assert len(result.items) == 1
    assert result.items[0].category_detailed == "FOOD_AND_DRINK_COFFEE"
    decoded_offset = service._decode_cursor(result.page.next_cursor)
    assert decoded_offset == 1


def test_list_for_household_rejects_inverted_date_ranges():
    service = TransactionLedgerService(transaction_repo=FakeTransactionRepo(0, []))

    with pytest.raises(ValidationError, match="start_date must be on or before end_date"):
        service.list_for_household(
            db=None,
            household_id=uuid4(),
            filters=TransactionLedgerFiltersDTO(
                start_date=datetime(2026, 6, 30, tzinfo=UTC).date(),
                end_date=datetime(2026, 6, 1, tzinfo=UTC).date(),
            ),
        )


def test_decode_cursor_rejects_invalid_values():
    service = TransactionLedgerService(transaction_repo=FakeTransactionRepo(0, []))

    with pytest.raises(ValidationError, match="Invalid cursor"):
        service._decode_cursor("not-a-real-cursor")
