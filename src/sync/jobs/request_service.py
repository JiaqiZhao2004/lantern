from uuid import UUID
from ...infrastructure import Session
from ...plaid.items.repository import (
    PlaidItemRepository,
    PlaidItemSyncState,
    PlaidItemStatus,
)
from .repository import SyncJobsRepository, SyncJob, JobType, JobStatus
from ...exceptions import ConflictError, NotFoundError, ValidationError


class SyncJobsRequestService:
    def __init__(
        self,
        plaid_items_repo: PlaidItemRepository,
        sync_jobs_repo: SyncJobsRepository,
    ):
        self.plaid_items_repo = plaid_items_repo
        self.sync_jobs_repo = sync_jobs_repo

    def _create_sync_job(self, db: Session, plaid_item_id: str, job_type: JobType):
        with db.begin():
            plaid_item = self.plaid_items_repo.get_by_plaid_item_id(
                db=db, plaid_item_id=plaid_item_id
            )
            if plaid_item is None:
                raise NotFoundError(detail="Plaid item not found")

            if not self.plaid_items_repo.is_active(plaid_item=plaid_item):
                return None  # ignore the job if item is revoked.

            if self.plaid_items_repo.is_unable_to_sync(plaid_item=plaid_item):
                return None  # ignore the job. Frontend will notify the user sync errors

            if self.plaid_items_repo.is_waiting_for_retry(plaid_item):
                return None  # ignore the job because the item will be eventually synced during the retry

            # If the item is attempting sync, update needs_resync = True and return
            # this is because the current sync may miss the latest transactions
            if self.plaid_items_repo.is_syncing(plaid_item):
                existing_job = (
                    self.sync_jobs_repo.get_queued_or_running_job_by_connection_id(
                        db=db, institution_connection_id=plaid_item.id
                    )
                )
                if existing_job is None:
                    # This should never happen, but just in case
                    raise ConflictError(detail="Could not create webhook resync job")

                if existing_job.status == JobStatus.QUEUED:
                    # A queued job means the sync hasn't started yet, so we don't need to mark need_resync.
                    return None
                # The job is running, so we mark needs_resync to True in case the current running job misses the latest transactions
                self.plaid_items_repo.mark_need_resync(db=db, plaid_item=plaid_item)
                return None

            # Otherwise, update sync_state as "syncing" and continue
            self.plaid_items_repo.mark_syncing(db=db, plaid_item=plaid_item)

            job = self.sync_jobs_repo.create(
                db=db,
                institution_connection_id=plaid_item.id,
                job_type=job_type,
            )
        db.refresh(job)
        return job

    def handle_onboarding(self, db: Session, plaid_item_id: str):
        return self._create_sync_job(
            db=db, plaid_item_id=plaid_item_id, job_type=JobType.ONBOARDING
        )

    def handle_webhook(self, db: Session, plaid_item_id: str):
        return self._create_sync_job(
            db=db, plaid_item_id=plaid_item_id, job_type=JobType.WEBHOOK
        )
