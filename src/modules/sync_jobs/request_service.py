from uuid import UUID
from ...infrastructure import Session
from ..institution_connections.repository import InstitutionConnectionRepository, InstitutionConnection
from .repository import SyncJobsRepository, SyncJob, SyncTrigger, JobStatus
from ...exceptions import ConflictError, NotFoundError, ValidationError


class SyncJobsRequestService:
    def __init__(
        self,
        connection_repo: InstitutionConnectionRepository,
        sync_jobs_repo: SyncJobsRepository,
    ):
        self.connection_repo = connection_repo
        self.sync_jobs_repo = sync_jobs_repo

    def _create_sync_job(self, db: Session, connection: InstitutionConnection, trigger: SyncTrigger):
        if not self.connection_repo.is_active(connection=connection):
            return None

        if self.connection_repo.is_unable_to_sync(connection=connection):
            return None

        if self.connection_repo.is_waiting_for_retry(connection):
            return None

        if trigger != SyncTrigger.INITIAL_LINK and self.connection_repo.is_syncing(connection):
            existing_job = (
                self.sync_jobs_repo.get_queued_or_running_job_by_connection_id(
                    db=db, institution_connection_id=connection.id
                )
            )
            if existing_job is None:
                raise ConflictError(detail="Could not create webhook resync job")

            if existing_job.status == JobStatus.QUEUED:
                return None
            self.connection_repo.mark_need_resync(db=db, connection=connection)
            return None

        self.connection_repo.mark_syncing(db=db, connection=connection)

        job = self.sync_jobs_repo.create(
            db=db,
            institution_connection_id=connection.id,
            trigger=trigger,
        )
        db.refresh(job)
        return job

    def create_initial_link_sync_job(self, db: Session, connection: InstitutionConnection):
        return self._create_sync_job(
            db=db, connection=connection, trigger=SyncTrigger.INITIAL_LINK
        )

    def create_webhook_sync_job(self, db: Session, plaid_item_id: str):
        connection = self.connection_repo.get_by_plaid_item_id(
            db=db, plaid_item_id=plaid_item_id
        )
        if connection is None:
            raise NotFoundError(detail="Institution connection not found")

        return self._create_sync_job(
            db=db, connection=connection, trigger=SyncTrigger.WEBHOOK
        )
