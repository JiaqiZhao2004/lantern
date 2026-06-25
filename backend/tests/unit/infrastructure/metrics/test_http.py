from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry

from src.infrastructure.metrics.http import install_http_metrics, metrics_response


def _app_with_metrics(session_factory=None):
    app = FastAPI()

    @app.get("/ok")
    async def ok():
        return {"status": "ok"}

    @app.get("/items/{item_id}")
    async def item(item_id: str):
        return {"item_id": item_id}

    @app.get("/boom")
    async def boom():
        return Response(status_code=500)

    @app.get("/health/live")
    async def health_live():
        return {"status": "ok"}

    registry = CollectorRegistry()
    install_http_metrics(
        app,
        registry=registry,
        session_factory=session_factory or _failing_session_factory,
    )

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return metrics_response(app)

    return app


def _failing_session_factory():
    raise RuntimeError("database unavailable")


def test_metrics_route_returns_prometheus_text():
    response = TestClient(_app_with_metrics()).get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


def test_successful_request_increments_request_counter():
    client = TestClient(_app_with_metrics())

    client.get("/ok")
    metrics = client.get("/metrics").text

    assert (
        'lantern_http_requests_total{method="GET",route="/ok",status_code="200"} 1.0'
        in metrics
    )


def test_500_response_increments_request_counter():
    client = TestClient(_app_with_metrics())

    client.get("/boom")
    metrics = client.get("/metrics").text

    assert (
        'lantern_http_requests_total{method="GET",route="/boom",status_code="500"} 1.0'
        in metrics
    )


def test_route_label_uses_template_not_raw_path():
    client = TestClient(_app_with_metrics())

    client.get("/items/abc-123")
    metrics = client.get("/metrics").text

    assert (
        'lantern_http_requests_total{method="GET",route="/items/{item_id}",status_code="200"} 1.0'
        in metrics
    )
    assert "abc-123" not in metrics


def test_health_and_metrics_routes_do_not_increment_request_counter():
    client = TestClient(_app_with_metrics())

    client.get("/health/live")
    client.get("/metrics")
    metrics = client.get("/metrics").text

    assert 'route="/health/live"' not in metrics
    assert 'route="/metrics"' not in metrics
