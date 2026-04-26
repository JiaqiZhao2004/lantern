from types import SimpleNamespace

from src.sync.runner.main import process


class FakeDb:
    def begin(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeSyncJobsExecutionService:
    def __init__(self, job=None):
        self.job = job
        self.successes = []
        self.failures = []

    def claim_next_due_job(self, db):
        return self.job

    def handle_success(self, db, job, plaid_item):
        self.successes.append((job, plaid_item))

    def handle_failure(self, db, job, plaid_item, error):
        self.failures.append((job, plaid_item, error))


class FakeTransactionService:
    def __init__(self, error=None):
        self.error = error
        self.sync_calls = []

    def sync(self, db, kms, plaid_client, plaid_item):
        self.sync_calls.append((db, kms, plaid_client, plaid_item))
        if self.error is not None:
            raise self.error


def _process(sync_service, transaction_service):
    return process(
        db=FakeDb(),
        kms=SimpleNamespace(),
        plaid_client=SimpleNamespace(),
        sync_jobs_execution_service=sync_service,
        transaction_service=transaction_service,
    )


def test_process_returns_false_when_no_job_is_due():
    sync_service = FakeSyncJobsExecutionService(job=None)
    transaction_service = FakeTransactionService()

    did_process = _process(sync_service, transaction_service)

    assert did_process is False
    assert transaction_service.sync_calls == []
    assert sync_service.successes == []
    assert sync_service.failures == []


def test_process_syncs_due_job_and_marks_success():
    plaid_item = SimpleNamespace()
    job = SimpleNamespace(institution_connection=plaid_item)
    sync_service = FakeSyncJobsExecutionService(job=job)
    transaction_service = FakeTransactionService()

    did_process = _process(sync_service, transaction_service)

    assert did_process is True
    assert transaction_service.sync_calls[0][3] is plaid_item
    assert sync_service.successes == [(job, plaid_item)]
    assert sync_service.failures == []


def test_process_marks_failure_when_transaction_sync_raises():
    plaid_item = SimpleNamespace()
    job = SimpleNamespace(institution_connection=plaid_item)
    error = RuntimeError("sync failed")
    sync_service = FakeSyncJobsExecutionService(job=job)
    transaction_service = FakeTransactionService(error=error)

    did_process = _process(sync_service, transaction_service)

    assert did_process is True
    assert sync_service.successes == []
    assert sync_service.failures == [(job, plaid_item, error)]
