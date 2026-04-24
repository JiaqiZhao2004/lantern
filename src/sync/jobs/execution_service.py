from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from ...infrastructure import Session
from ...plaid.items.repository import PlaidItemRepository, PlaidItem
from .repository import SyncJobsRepository, SyncJob, JobType, SyncErrorType, JobStatus
from ...exceptions import ConflictError, NotFoundError, ValidationError
from datetime import timedelta


def is_retryable(error_type: SyncErrorType):
    # TODO
    if error_type == SyncErrorType.TRANSIENT or error_type == SyncErrorType.RATE_LIMIT:
        return True
    return False


def infer_error_type(error):
    # TODO
    return SyncErrorType.UNKNOWN


def compute_backoff(attempt_count: int):
    return datetime.now(timezone.utc) + timedelta(minutes=2**attempt_count)


class SyncJobsExecutionService:
    def __init__(
        self,
        plaid_items_repo: PlaidItemRepository,
        sync_jobs_repo: SyncJobsRepository,
    ):
        self.plaid_items_repo = plaid_items_repo
        self.sync_jobs_repo = sync_jobs_repo

    def claim_next_due_job(self, db: Session):
        job = self.sync_jobs_repo.claim_next_due_job(db=db)
        if job is None:
            return None
        job = self.sync_jobs_repo.set_running(db=db, job=job)
        self.plaid_items_repo.mark_syncing(db=db, plaid_item=job.institution_connection)
        return job

    def handle_success(self, db: Session, job: SyncJob, plaid_item: PlaidItem):
        self.sync_jobs_repo.set_succeeded(db=db, job=job)
        self.plaid_items_repo.mark_in_sync(db=db, plaid_item=plaid_item)
        if plaid_item.needs_resync:
            self.sync_jobs_repo.create(
                db=db, institution_connection_id=plaid_item.id, job_type=job.job_type
            )
            self.plaid_items_repo.clear_need_resync(db=db, plaid_item=plaid_item)

    def handle_failure(self, db: Session, job: SyncJob, plaid_item: PlaidItem, error):

        # if error is retryable and attempt count < 3, schedule retry
        error_type = infer_error_type(error)
        if is_retryable(error_type=error_type) and job.attempt_count < 3:
            next_attempt_at = compute_backoff(job.attempt_count)
            self.sync_jobs_repo.schedule_retry(
                db=db,
                job=job,
                next_attempt_at=next_attempt_at,
                last_error=str(error),
                last_error_type=error_type,
            )
            self.plaid_items_repo.mark_sync_retry_scheduled(
                db=db, plaid_item=plaid_item, error=str(error)
            )
        # else, mark as dead letter and update plaid item sync state to disabled
        else:
            self.sync_jobs_repo.set_dead_letter(
                db=db,
                job=job,
                last_error=str(error),
                last_error_type=error_type,
            )
            if error_type == SyncErrorType.REAUTH_REQUIRED:
                self.plaid_items_repo.mark_sync_needs_reauth(
                    db=db, plaid_item=job.institution_connection, error=str(error)
                )
            elif error_type == SyncErrorType.UNKNOWN:
                self.plaid_items_repo.mark_sync_disabled(
                    db=db, plaid_item=job.institution_connection, error=str(error)
                )
