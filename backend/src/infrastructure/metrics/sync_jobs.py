from collections.abc import Callable
from datetime import datetime, timezone

from prometheus_client import CollectorRegistry, Gauge, REGISTRY
from sqlalchemy import case, func

from src.modules.sync_jobs.models import JobStatus, SyncJob


class SyncJobMetrics:
    def __init__(self, registry: CollectorRegistry = REGISTRY):
        self.jobs_by_status = Gauge(
            "lantern_sync_jobs_by_status",
            "SyncJobs by status.",
            ["status"],
            registry=registry,
        )
        self.oldest_queued_age_seconds = Gauge(
            "lantern_sync_jobs_oldest_queued_age_seconds",
            "Age in seconds of the oldest queued SyncJob.",
            registry=registry,
        )
        self.oldest_running_age_seconds = Gauge(
            "lantern_sync_jobs_oldest_running_age_seconds",
            "Age in seconds of the oldest running SyncJob.",
            registry=registry,
        )
        self.due_queued_total = Gauge(
            "lantern_sync_jobs_due_queued_total",
            "Queued SyncJobs due to run now.",
            registry=registry,
        )
        self.last_dead_letter_timestamp_seconds = Gauge(
            "lantern_sync_jobs_last_dead_letter_timestamp_seconds",
            "Unix timestamp for the most recently dead-lettered SyncJob.",
            registry=registry,
        )
        self.completed_total = Gauge(
            "lantern_sync_jobs_completed_total",
            "Succeeded SyncJobs.",
            registry=registry,
        )
        self.last_completed_age_hours = Gauge(
            "lantern_sync_jobs_last_completed_age_hours",
            "Age in hours of the most recently succeeded SyncJob.",
            registry=registry,
        )
        self.collection_success = Gauge(
            "lantern_sync_jobs_metrics_collection_success",
            "Whether SyncJob metrics collection succeeded on the last scrape.",
            registry=registry,
        )

    def collect(self, session_factory: Callable) -> None:
        try:
            with session_factory() as db:
                now = datetime.now(timezone.utc)
                status_counts = {
                    status.value: 0
                    for status in JobStatus
                }
                for status, count in (
                    db.query(SyncJob.status, func.count(SyncJob.id))
                    .group_by(SyncJob.status)
                    .all()
                ):
                    status_counts[str(status.value if hasattr(status, "value") else status)] = count

                (
                    oldest_queued_at,
                    oldest_running_at,
                    due_queued_total,
                    last_dead_letter_at,
                    completed_total,
                    last_completed_at,
                ) = (
                    db.query(
                        func.min(
                            case(
                                (SyncJob.status == JobStatus.QUEUED, SyncJob.created_at),
                                else_=None,
                            )
                        ),
                        func.min(
                            case(
                                (SyncJob.status == JobStatus.RUNNING, SyncJob.started_at),
                                else_=None,
                            )
                        ),
                        func.count(
                            case(
                                (
                                    (SyncJob.status == JobStatus.QUEUED)
                                    & (SyncJob.next_attempt_at <= func.now()),
                                    SyncJob.id,
                                ),
                                else_=None,
                            )
                        ),
                        func.max(
                            case(
                                (
                                    SyncJob.status == JobStatus.DEAD_LETTER,
                                    SyncJob.finished_at,
                                ),
                                else_=None,
                            )
                        ),
                        func.count(
                            case(
                                (SyncJob.status == JobStatus.SUCCEEDED, SyncJob.id),
                                else_=None,
                            )
                        ),
                        func.max(
                            case(
                                (
                                    SyncJob.status == JobStatus.SUCCEEDED,
                                    SyncJob.finished_at,
                                ),
                                else_=None,
                            )
                        ),
                    ).one()
                )

            for status, count in status_counts.items():
                self.jobs_by_status.labels(status=status).set(count)
            self.oldest_queued_age_seconds.set(
                _age_seconds(now=now, timestamp=oldest_queued_at)
            )
            self.oldest_running_age_seconds.set(
                _age_seconds(now=now, timestamp=oldest_running_at)
            )
            self.due_queued_total.set(due_queued_total)
            self.last_dead_letter_timestamp_seconds.set(
                _timestamp_seconds(last_dead_letter_at)
            )
            self.completed_total.set(completed_total)
            self.last_completed_age_hours.set(
                _age_hours(now=now, timestamp=last_completed_at)
            )
            self.collection_success.set(1)
        except Exception:
            self.collection_success.set(0)


def _age_seconds(now: datetime, timestamp: datetime | None) -> float:
    if timestamp is None:
        return 0
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return max(0, (now - timestamp.astimezone(timezone.utc)).total_seconds())


def _age_hours(now: datetime, timestamp: datetime | None) -> float:
    return _age_seconds(now=now, timestamp=timestamp) / 3600


def _timestamp_seconds(timestamp: datetime | None) -> float:
    if timestamp is None:
        return 0
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc).timestamp()
