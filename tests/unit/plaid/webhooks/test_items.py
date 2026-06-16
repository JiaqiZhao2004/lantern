from types import SimpleNamespace
from uuid import uuid4

from src.modules.plaid_webhooks.items_service import PlaidItemsWebhookService
from src.modules.plaid_webhooks.schema import PlaidWebhookPayload


class FakeDb:
    def begin(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeItemRepo:
    def __init__(self, item=None):
        self.item = item
        self.needs_reauth_errors = []
        self.cleared = False
        self.active = False
        self.revoked = False

    def get_by_plaid_item_id(self, **_):
        return self.item

    def mark_sync_needs_reauth(self, db, plaid_item, error):
        plaid_item.sync_state = "needs_reauth"
        plaid_item.last_sync_error = error
        self.needs_reauth_errors.append(error)
        return plaid_item

    def mark_item_active(self, db, plaid_item):
        plaid_item.status = "active"
        self.active = True
        return plaid_item

    def clear_sync_error(self, db, plaid_item):
        plaid_item.sync_state = "in_sync"
        plaid_item.last_sync_error = None
        self.cleared = True
        return plaid_item

    def mark_item_revoked_and_disabled(self, db, plaid_item, error):
        plaid_item.status = "revoked"
        plaid_item.sync_state = "disabled"
        plaid_item.last_sync_error = error
        self.revoked = True
        return plaid_item


class FakeAccountRepo:
    def __init__(self):
        self.inactivated = []

    def mark_inactive_by_plaid_id(self, db, item_id, plaid_account_id):
        self.inactivated.append((item_id, plaid_account_id))
        return SimpleNamespace(id=uuid4(), is_active=False)


class FakeSyncJobsRequestService:
    def __init__(self):
        self.webhook_item_ids = []

    def create_webhook_sync_job(self, db, plaid_item_id):
        self.webhook_item_ids.append(plaid_item_id)
        return SimpleNamespace(id=uuid4())


class FakeSyncJobsRepo:
    def __init__(self):
        self.cancelled_connection_ids = []

    def cancel_queued_or_running_for_connection(
        self,
        db,
        institution_connection_id,
        last_error=None,
    ):
        self.cancelled_connection_ids.append((institution_connection_id, last_error))


def _service(item=None):
    item_repo = FakeItemRepo(item=item)
    account_repo = FakeAccountRepo()
    sync_request_service = FakeSyncJobsRequestService()
    sync_jobs_repo = FakeSyncJobsRepo()
    service = PlaidItemsWebhookService(
        plaid_item_repo=item_repo,
        plaid_account_repo=account_repo,
        sync_jobs_request_service=sync_request_service,
        sync_jobs_repo=sync_jobs_repo,
    )
    return service, item_repo, account_repo, sync_request_service, sync_jobs_repo


def test_item_login_required_marks_needs_reauth_and_cancels_jobs():
    item = SimpleNamespace(id=uuid4(), plaid_item_id="item-1")
    service, item_repo, _, _, sync_jobs_repo = _service(item=item)

    service.handle(
        db=FakeDb(),
        payload=PlaidWebhookPayload(
            webhook_type="ITEM",
            webhook_code="ERROR",
            item_id="item-1",
            error={"error_code": "ITEM_LOGIN_REQUIRED"},
        ),
    )

    assert item_repo.needs_reauth_errors == ["ITEM_LOGIN_REQUIRED"]
    assert sync_jobs_repo.cancelled_connection_ids == [
        (item.id, "ITEM_LOGIN_REQUIRED")
    ]


def test_login_repaired_clears_error_and_enqueues_sync():
    item = SimpleNamespace(id=uuid4(), plaid_item_id="item-1")
    service, item_repo, _, sync_request_service, _ = _service(item=item)

    service.handle(
        db=FakeDb(),
        payload=PlaidWebhookPayload(
            webhook_type="ITEM",
            webhook_code="LOGIN_REPAIRED",
            item_id="item-1",
        ),
    )

    assert item_repo.active is True
    assert item_repo.cleared is True
    assert sync_request_service.webhook_item_ids == ["item-1"]


def test_pending_disconnect_marks_needs_reauth_and_cancels_jobs():
    item = SimpleNamespace(id=uuid4(), plaid_item_id="item-1")
    service, item_repo, _, _, sync_jobs_repo = _service(item=item)

    service.handle(
        db=FakeDb(),
        payload=PlaidWebhookPayload(
            webhook_type="ITEM",
            webhook_code="PENDING_DISCONNECT",
            item_id="item-1",
        ),
    )

    assert item_repo.needs_reauth_errors == ["PENDING_DISCONNECT"]
    assert sync_jobs_repo.cancelled_connection_ids == [
        (item.id, "PENDING_DISCONNECT")
    ]


def test_item_revoked_marks_item_revoked_and_cancels_jobs():
    item = SimpleNamespace(id=uuid4(), plaid_item_id="item-1")
    service, item_repo, _, _, sync_jobs_repo = _service(item=item)

    service.handle(
        db=FakeDb(),
        payload=PlaidWebhookPayload(
            webhook_type="ITEM",
            webhook_code="USER_PERMISSION_REVOKED",
            item_id="item-1",
        ),
    )

    assert item_repo.revoked is True
    assert sync_jobs_repo.cancelled_connection_ids == [
        (item.id, "USER_PERMISSION_REVOKED")
    ]


def test_account_revoked_marks_account_inactive():
    item = SimpleNamespace(id=uuid4(), plaid_item_id="item-1")
    service, _, account_repo, _, _ = _service(item=item)

    service.handle(
        db=FakeDb(),
        payload=PlaidWebhookPayload(
            webhook_type="ITEM",
            webhook_code="USER_ACCOUNT_REVOKED",
            item_id="item-1",
            account_id="account-1",
        ),
    )

    assert account_repo.inactivated == [(item.id, "account-1")]


def test_acknowledged_item_webhooks_are_accepted_without_side_effects():
    service, _, _, sync_request_service, _ = _service()

    service.handle(
        db=FakeDb(),
        payload=PlaidWebhookPayload(
            webhook_type="ITEM",
            webhook_code="WEBHOOK_UPDATE_ACKNOWLEDGED",
            item_id="item-1",
        ),
    )

    assert sync_request_service.webhook_item_ids == []


def test_unknown_item_webhook_is_accepted_without_side_effects():
    service, _, _, sync_request_service, _ = _service()

    service.handle(
        db=FakeDb(),
        payload=PlaidWebhookPayload(
            webhook_type="ITEM",
            webhook_code="SOMETHING_NEW",
            item_id="item-1",
        ),
    )

    assert sync_request_service.webhook_item_ids == []
