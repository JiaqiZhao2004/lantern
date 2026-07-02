from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from prometheus_client import CollectorRegistry, generate_latest

from src.infrastructure.metrics.sync_jobs import SyncJobMetrics
from src.modules.sync_jobs.models import JobStatus


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def group_by(self, *_):
        return self

    def all(self):
        return self.result

    def one(self):
        return self.result


class FakeDb:
    def __init__(self, now):
        self.now = now
        self.query_count = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def query(self, *_):
        self.query_count += 1
        if self.query_count == 1:
            return FakeQuery(
                [
                    (JobStatus.QUEUED, 2),
                    (JobStatus.RUNNING, 1),
                    (JobStatus.DEAD_LETTER, 1),
                ]
            )

        return FakeQuery(
            (
                self.now - timedelta(minutes=90),
                self.now - timedelta(minutes=30),
                2,
                self.now - timedelta(hours=3),
                4,
                self.now - timedelta(minutes=5),
            )
        )


def test_sync_job_metrics_collects_aggregate_gauges(monkeypatch):
    now = datetime(2026, 6, 25, 12, 0, tzinfo=timezone.utc)
    registry = CollectorRegistry()
    metrics = SyncJobMetrics(registry=registry)

    monkeypatch.setattr(
        "src.infrastructure.metrics.sync_jobs.datetime",
        SimpleNamespace(now=lambda _: now),
    )

    metrics.collect(session_factory=lambda: FakeDb(now))
    output = generate_latest(registry).decode()

    assert 'lantern_sync_jobs_by_status{status="queued"} 2.0' in output
    assert 'lantern_sync_jobs_by_status{status="running"} 1.0' in output
    assert 'lantern_sync_jobs_by_status{status="succeeded"} 0.0' in output
    assert "lantern_sync_jobs_oldest_queued_age_seconds 5400.0" in output
    assert "lantern_sync_jobs_oldest_running_age_seconds 1800.0" in output
    assert "lantern_sync_jobs_due_queued_total 2.0" in output
    assert "lantern_sync_jobs_completed_total 4.0" in output
    assert "lantern_sync_jobs_last_completed_age_hours 0.08333333333333333" in output
    assert "lantern_sync_jobs_metrics_collection_success 1.0" in output


def test_sync_job_metrics_marks_collection_failure_without_clearing_gauges():
    registry = CollectorRegistry()
    metrics = SyncJobMetrics(registry=registry)

    metrics.jobs_by_status.labels(status="queued").set(3)
    metrics.collect(session_factory=lambda: (_ for _ in ()).throw(RuntimeError("db down")))
    output = generate_latest(registry).decode()

    assert 'lantern_sync_jobs_by_status{status="queued"} 3.0' in output
    assert "lantern_sync_jobs_metrics_collection_success 0.0" in output
