from types import SimpleNamespace
from uuid import uuid4

from src.modules.sync_jobs.models import JobStatus, SyncTrigger
from src.modules.sync_jobs.request_service import (
    SyncJobsRequestService,
)


class FakeDb:
    def begin(self):
        return self

    def refresh(self, _):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeConnectionRepo:
    def __init__(self, connection):
        self.connection = connection
        self.marked_syncing = False
        self.marked_needs_resync = False

    def get_by_plaid_item_id(self, db, plaid_item_id):
        return self.connection

    def is_active(self, connection):
        return True

    def is_unable_to_sync(self, connection):
        return False

    def is_waiting_for_retry(self, connection):
        return False

    def is_syncing(self, connection):
        return connection.syncing

    def mark_syncing(self, db, connection):
        connection.syncing = True
        self.marked_syncing = True
        return connection

    def mark_need_resync(self, db, connection):
        connection.needs_resync = True
        self.marked_needs_resync = True
        return connection


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

    def create(self, db, institution_connection_id, trigger, subject=None):
        job = SimpleNamespace(
            id=uuid4(),
            institution_connection_id=institution_connection_id,
            trigger=trigger,
        )
        self.created.append(job)
        return job


def test_webhook_creates_job_for_idle_connection():
    connection = SimpleNamespace(id=uuid4(), syncing=False)
    connection_repo = FakeConnectionRepo(connection=connection)
    sync_repo = FakeSyncJobsRepo()
    service = SyncJobsRequestService(
        connection_repo=connection_repo,
        sync_jobs_repo=sync_repo,
    )

    job = service.create_webhook_sync_job(db=FakeDb(), plaid_item_id="item-1")

    assert job.trigger == SyncTrigger.WEBHOOK
    assert connection_repo.marked_syncing is True
    assert len(sync_repo.created) == 1


def test_duplicate_webhook_while_queued_is_ignored():
    connection = SimpleNamespace(id=uuid4(), syncing=True, needs_resync=False)
    connection_repo = FakeConnectionRepo(connection=connection)
    sync_repo = FakeSyncJobsRepo(existing_job=SimpleNamespace(status=JobStatus.QUEUED))
    service = SyncJobsRequestService(
        connection_repo=connection_repo,
        sync_jobs_repo=sync_repo,
    )

    job = service.create_webhook_sync_job(db=FakeDb(), plaid_item_id="item-1")

    assert job is None
    assert connection.needs_resync is False
    assert sync_repo.created == []


def test_duplicate_webhook_while_running_sets_needs_resync():
    connection = SimpleNamespace(id=uuid4(), syncing=True, needs_resync=False)
    connection_repo = FakeConnectionRepo(connection=connection)
    sync_repo = FakeSyncJobsRepo(existing_job=SimpleNamespace(status=JobStatus.RUNNING))
    service = SyncJobsRequestService(
        connection_repo=connection_repo,
        sync_jobs_repo=sync_repo,
    )

    job = service.create_webhook_sync_job(db=FakeDb(), plaid_item_id="item-1")

    assert job is None
    assert connection.needs_resync is True
    assert connection_repo.marked_needs_resync is True
    assert sync_repo.created == []
