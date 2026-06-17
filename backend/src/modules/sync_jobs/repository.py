from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from .models import SyncJob, SyncTrigger, SyncSubject, JobStatus, SyncErrorType


class SyncJobsRepository:

    def create(
        self,
        db: Session,
        institution_connection_id: UUID,
        trigger: SyncTrigger,
        subject: SyncSubject = SyncSubject.TRANSACTIONS,
    ):
        job = SyncJob(
            institution_connection_id=institution_connection_id,
            trigger=trigger,
            subject=subject,
            next_attempt_at=datetime.now(timezone.utc),
        )
        db.add(job)
        db.flush()
        return job

    def claim_next_due_job(self, db: Session):
        return (
            db.query(SyncJob)
            .filter(
                SyncJob.status == "queued",
                SyncJob.next_attempt_at <= func.now(),
            )
            .order_by(SyncJob.created_at)
            .with_for_update(skip_locked=True)
            .first()
        )

    def get_queued_or_running_job_by_connection_id(
        self, db: Session, institution_connection_id: UUID
    ):
        return (
            db.query(SyncJob)
            .filter(
                SyncJob.institution_connection_id == institution_connection_id,
                SyncJob.status.in_(["queued", "running"]),
            )
            .first()
        )

    def set_running(self, db: Session, job: SyncJob):
        job.status = JobStatus.RUNNING
        job.attempt_count += 1
        job.started_at = datetime.now(timezone.utc)
        db.flush()
        return job

    def set_succeeded(self, db: Session, job: SyncJob):
        job.status = JobStatus.SUCCEEDED
        job.finished_at = datetime.now(timezone.utc)
        db.flush()
        return job

    def schedule_retry(
        self,
        db: Session,
        job: SyncJob,
        next_attempt_at: datetime,
        last_error: str | None = None,
        last_error_type: SyncErrorType | None = None,
    ):
        job.status = JobStatus.QUEUED
        job.started_at = None
        job.finished_at = None
        job.next_attempt_at = next_attempt_at.astimezone(timezone.utc)
        job.last_error = last_error
        job.last_error_type = last_error_type
        db.flush()
        return job

    def set_dead_letter(
        self,
        db: Session,
        job: SyncJob,
        last_error: str | None = None,
        last_error_type: SyncErrorType | None = None,
    ):
        job.status = JobStatus.DEAD_LETTER
        job.finished_at = datetime.now(timezone.utc)
        job.last_error = last_error
        job.last_error_type = last_error_type
        db.flush()
        return job

    def set_cancelled(
        self,
        db: Session,
        job: SyncJob,
        last_error: str | None = None,
    ):
        job.status = JobStatus.CANCELLED
        job.finished_at = datetime.now(timezone.utc)
        job.last_error = last_error
        db.flush()
        return job

    def cancel_queued_or_running_for_connection(
        self,
        db: Session,
        institution_connection_id: UUID,
        last_error: str | None = None,
    ):
        jobs = (
            db.query(SyncJob)
            .filter(
                SyncJob.institution_connection_id == institution_connection_id,
                SyncJob.status.in_([JobStatus.QUEUED, JobStatus.RUNNING]),
            )
            .all()
        )
        for job in jobs:
            self.set_cancelled(db=db, job=job, last_error=last_error)
        return jobs
