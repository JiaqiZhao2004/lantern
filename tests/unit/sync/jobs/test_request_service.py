from types import SimpleNamespace
from uuid import uuid4

from src.sync.jobs.models import JobStatus, JobType
from src.sync.jobs.request_service import SyncJobsRequestService


class FakeDb:
    def begin(self):
        return self

    def refresh(self, _):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakePlaidItemRepo:
    def __init__(self, item):
        self.item = item
        self.marked_syncing = False
        self.marked_needs_resync = False

    def get_by_plaid_item_id(self, db, plaid_item_id):
        return self.item

    def is_active(self, plaid_item):
        return True

    def is_unable_to_sync(self, plaid_item):
        return False

    def is_waiting_for_retry(self, plaid_item):
        return False

    def is_syncing(self, plaid_item):
        return plaid_item.syncing

    def mark_syncing(self, db, plaid_item):
        plaid_item.syncing = True
        self.marked_syncing = True
        return plaid_item

    def mark_need_resync(self, db, plaid_item):
        plaid_item.needs_resync = True
        self.marked_needs_resync = True
        return plaid_item


class FakeSyncJobsRepo:
    def __init__(self, existing_job=None):
        self.existing_job = existing_job
        self.created = []

    def get_queued_or_running_job_by_connection_id(
        self,
        db,
        institution_connection_id,
    ):
        return self.existing_job

    def create(self, db, institution_connection_id, job_type):
        job = SimpleNamespace(
            id=uuid4(),
            institution_connection_id=institution_connection_id,
            job_type=job_type,
        )
        self.created.append(job)
        return job


def test_webhook_creates_job_for_idle_item():
    item = SimpleNamespace(id=uuid4(), syncing=False)
    item_repo = FakePlaidItemRepo(item=item)
    sync_repo = FakeSyncJobsRepo()
    service = SyncJobsRequestService(
        plaid_items_repo=item_repo,
        sync_jobs_repo=sync_repo,
    )

    job = service.handle_webhook(db=FakeDb(), plaid_item_id="item-1")

    assert job.job_type == JobType.WEBHOOK
    assert item_repo.marked_syncing is True
    assert len(sync_repo.created) == 1


def test_duplicate_webhook_while_queued_is_ignored():
    item = SimpleNamespace(id=uuid4(), syncing=True, needs_resync=False)
    item_repo = FakePlaidItemRepo(item=item)
    sync_repo = FakeSyncJobsRepo(
        existing_job=SimpleNamespace(status=JobStatus.QUEUED)
    )
    service = SyncJobsRequestService(
        plaid_items_repo=item_repo,
        sync_jobs_repo=sync_repo,
    )

    job = service.handle_webhook(db=FakeDb(), plaid_item_id="item-1")

    assert job is None
    assert item.needs_resync is False
    assert sync_repo.created == []


def test_duplicate_webhook_while_running_sets_needs_resync():
    item = SimpleNamespace(id=uuid4(), syncing=True, needs_resync=False)
    item_repo = FakePlaidItemRepo(item=item)
    sync_repo = FakeSyncJobsRepo(
        existing_job=SimpleNamespace(status=JobStatus.RUNNING)
    )
    service = SyncJobsRequestService(
        plaid_items_repo=item_repo,
        sync_jobs_repo=sync_repo,
    )

    job = service.handle_webhook(db=FakeDb(), plaid_item_id="item-1")

    assert job is None
    assert item.needs_resync is True
    assert item_repo.marked_needs_resync is True
    assert sync_repo.created == []
