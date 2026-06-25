from collections.abc import Callable
from time import perf_counter

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    REGISTRY,
    generate_latest,
)
from starlette.routing import Match

from src.infrastructure.db.database import SessionLocal
from src.infrastructure.metrics.sync_jobs import SyncJobMetrics

EXCLUDED_PATHS = frozenset({"/metrics", "/health/live", "/health/ready"})


def _resolve_route_template(app: FastAPI, request: Request) -> str:
    for route in app.routes:
        match, _ = route.matches(request.scope)
        if match in {Match.FULL, Match.PARTIAL}:
            return getattr(route, "path", "unmatched")
    return "unmatched"


class HttpMetrics:
    def __init__(
        self,
        registry: CollectorRegistry = REGISTRY,
        excluded_paths: frozenset[str] = EXCLUDED_PATHS,
    ):
        self.excluded_paths = excluded_paths
        self.requests_total = Counter(
            "lantern_http_requests_total",
            "Total HTTP requests served by the backend.",
            ["method", "route", "status_code"],
            registry=registry,
        )
        self.request_duration_seconds = Histogram(
            "lantern_http_request_duration_seconds",
            "Backend HTTP request duration in seconds.",
            ["method", "route", "status_code"],
            registry=registry,
        )
        self.requests_in_progress = Gauge(
            "lantern_http_requests_in_progress",
            "Backend HTTP requests currently in progress.",
            ["method", "route"],
            registry=registry,
        )

    def should_skip(self, path: str) -> bool:
        return path in self.excluded_paths


def install_http_metrics(
    app: FastAPI,
    *,
    registry: CollectorRegistry = REGISTRY,
    session_factory: Callable = SessionLocal,
) -> None:
    http_metrics = HttpMetrics(registry=registry)
    sync_job_metrics = SyncJobMetrics(registry=registry)
    app.state.metrics_registry = registry
    app.state.sync_job_metrics = sync_job_metrics

    @app.middleware("http")
    async def record_http_metrics(request: Request, call_next):
        if http_metrics.should_skip(request.url.path):
            return await call_next(request)

        method = request.method
        route = _resolve_route_template(app, request)
        start = perf_counter()
        http_metrics.requests_in_progress.labels(method=method, route=route).inc()

        try:
            response = await call_next(request)
        except Exception:
            status_code = "500"
            elapsed = perf_counter() - start
            http_metrics.requests_total.labels(
                method=method,
                route=route,
                status_code=status_code,
            ).inc()
            http_metrics.request_duration_seconds.labels(
                method=method,
                route=route,
                status_code=status_code,
            ).observe(elapsed)
            raise
        else:
            status_code = str(response.status_code)
            elapsed = perf_counter() - start
            http_metrics.requests_total.labels(
                method=method,
                route=route,
                status_code=status_code,
            ).inc()
            http_metrics.request_duration_seconds.labels(
                method=method,
                route=route,
                status_code=status_code,
            ).observe(elapsed)
            return response
        finally:
            http_metrics.requests_in_progress.labels(method=method, route=route).dec()

    app.state.collect_sync_job_metrics = lambda: sync_job_metrics.collect(
        session_factory=session_factory
    )


def metrics_response(app: FastAPI) -> Response:
    collect_sync_job_metrics = getattr(app.state, "collect_sync_job_metrics", None)
    if collect_sync_job_metrics is not None:
        collect_sync_job_metrics()

    registry = getattr(app.state, "metrics_registry", REGISTRY)
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
