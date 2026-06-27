from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.exceptions import NotFoundError
from src.modules.accounts.service import AccountService


class FakeAccountRepo:
    def __init__(self, account=None):
        self.account = account
        self.get_calls = []
        self.set_calls = []

    def get_household_account(self, db, *, household_id, account_id):
        self.get_calls.append(
            {
                "db": db,
                "household_id": household_id,
                "account_id": account_id,
            }
        )
        return self.account

    def set_query_tracking_enabled(self, db, *, account, is_query_tracking_enabled):
        self.set_calls.append(
            {
                "db": db,
                "account": account,
                "is_query_tracking_enabled": is_query_tracking_enabled,
            }
        )
        account.is_query_tracking_enabled = is_query_tracking_enabled
        return account


def test_set_query_tracking_enabled_updates_household_account():
    db = object()
    household_id = uuid4()
    account_id = uuid4()
    account = SimpleNamespace(id=account_id, is_query_tracking_enabled=True)
    repo = FakeAccountRepo(account=account)
    service = AccountService(account_repo=repo)

    result = service.set_query_tracking_enabled(
        db=db,
        household_id=household_id,
        account_id=account_id,
        is_query_tracking_enabled=False,
    )

    assert result is account
    assert result.is_query_tracking_enabled is False
    assert repo.get_calls == [
        {
            "db": db,
            "household_id": household_id,
            "account_id": account_id,
        }
    ]
    assert repo.set_calls == [
        {
            "db": db,
            "account": account,
            "is_query_tracking_enabled": False,
        }
    ]


def test_set_query_tracking_enabled_raises_for_unknown_account():
    service = AccountService(account_repo=FakeAccountRepo(account=None))

    with pytest.raises(NotFoundError, match="Account not found"):
        service.set_query_tracking_enabled(
            db=object(),
            household_id=uuid4(),
            account_id=uuid4(),
            is_query_tracking_enabled=True,
        )
