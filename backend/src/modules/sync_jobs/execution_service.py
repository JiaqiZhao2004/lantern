from datetime import datetime, timezone, timedelta
from ...infrastructure import Session
from ..institution_connections.repository import InstitutionConnectionRepository, InstitutionConnection
from .repository import SyncJobsRepository, SyncJob, SyncErrorType, JobStatus
from ...exceptions import ConflictError, NotFoundError, ValidationError


def is_retryable(error_type: SyncErrorType):
    if error_type == SyncErrorType.TRANSIENT or error_type == SyncErrorType.RATE_LIMIT:
        return True
    return False


def infer_error_type(error):
    return SyncErrorType.UNKNOWN


def compute_backoff(attempt_count: int):
    return datetime.now(timezone.utc) + timedelta(minutes=2**attempt_count)


class SyncJobsExecutionService:
    def __init__(
        self,
        connection_repo: InstitutionConnectionRepository,
        sync_jobs_repo: SyncJobsRepository,
    ):
        self.connection_repo = connection_repo
        self.sync_jobs_repo = sync_jobs_repo

    def claim_next_due_job(self, db: Session):
        while True:
            job = self.sync_jobs_repo.claim_next_due_job(db=db)
            if job is None:
                return None

            connection = job.institution_connection
            if not self.connection_repo.is_active(
                connection
            ) or self.connection_repo.is_unable_to_sync(connection):
                self.sync_jobs_repo.set_cancelled(
                    db=db,
                    job=job,
                    last_error="Connection is not eligible for sync",
                )
                continue

            job = self.sync_jobs_repo.set_running(db=db, job=job)
            self.connection_repo.mark_syncing(db=db, connection=connection)
            return job

    def handle_success(self, db: Session, job: SyncJob, connection: InstitutionConnection):
        self.sync_jobs_repo.set_succeeded(db=db, job=job)
        if not self.connection_repo.is_active(
            connection
        ) or self.connection_repo.is_unable_to_sync(connection):
            return

        self.connection_repo.mark_in_sync(db=db, connection=connection)
        if connection.needs_resync:
            self.sync_jobs_repo.create(
                db=db, institution_connection_id=connection.id, trigger=job.trigger
            )
            self.connection_repo.clear_need_resync(db=db, connection=connection)

    def handle_failure(self, db: Session, job: SyncJob, connection: InstitutionConnection, error):
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
            self.connection_repo.mark_sync_retry_scheduled(
                db=db, connection=connection, error=str(error)
            )
        else:
            self.sync_jobs_repo.set_dead_letter(
                db=db,
                job=job,
                last_error=str(error),
                last_error_type=error_type,
            )
            if error_type == SyncErrorType.REAUTH_REQUIRED:
                self.connection_repo.mark_sync_needs_reauth(
                    db=db, connection=job.institution_connection, error=str(error)
                )
            elif error_type == SyncErrorType.UNKNOWN:
                self.connection_repo.mark_sync_disabled(
                    db=db, connection=job.institution_connection, error=str(error)
                )
