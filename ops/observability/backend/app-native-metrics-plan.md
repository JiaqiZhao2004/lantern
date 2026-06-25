# App-Native Metrics Plan

This plan adds app-native observability for Lantern's backend HTTP surface and
transaction sync worker while keeping the existing observability stack as the
runtime boundary.

## Scope

In scope:

- FastAPI `/metrics` exposed only on the private backend Docker network.
- HTTP request count, 5xx count, latency, and in-progress request metrics.
- Prometheus scrape config for `backend:8000/metrics`.
- Low-volume 5xx alerts.
- Worker heartbeat metric through the existing node_exporter textfile collector.
- Aggregate SyncJob gauges collected through backend `/metrics`.
- Worker/SyncJob alerts tuned for low app volume.
- Two Grafana panels on the existing overview dashboard.
- Required automated tests and local Docker Compose verification.
- ADR for the chosen app-native metrics topology.

Out of scope:

- Public or nginx-routed `/metrics`.
- Personal-token or browser-token synthetic production API checks.
- Detailed worker event counters by trigger, result, or upstream failure type.
- A dedicated worker HTTP metrics server.
- A dedicated SyncJob exporter process.
- Sync Trigger naming cleanup between `onboarding` and `initial_link`.
- Log aggregation and tracing.

## Decisions

### Backend HTTP Metrics

Add a small infrastructure module:

```text
backend/src/infrastructure/metrics/http.py
```

Responsibilities:

- define Prometheus collectors
- install FastAPI middleware
- expose a helper for the `/metrics` response
- skip `/metrics`, `/health/live`, and `/health/ready`
- use FastAPI route templates as route labels

Metric labels:

```text
method
route
status_code
```

Do not add labels for User, Household, InstitutionConnection, raw path,
exception text, request body, or query string.

Initial HTTP metrics:

```text
lantern_http_requests_total{method,route,status_code}
lantern_http_request_duration_seconds_bucket{method,route,status_code,le}
lantern_http_requests_in_progress{method,route}
```

Health endpoints stay monitored by the existing blackbox checks. They are
excluded from HTTP request/error-rate metrics so routine probes do not dilute
low-volume API error percentages.

### Metrics Route

Add a private metrics route in `backend/src/server.py`:

```python
@app.get("/metrics", include_in_schema=False)
async def metrics():
    return metrics_response()
```

Prometheus should scrape the backend container directly over the shared Docker
network:

```text
backend:8000/metrics
```

Do not route `/metrics` through nginx, Cloudflare, CloudFront, or any public
origin path.

### HTTP Alerts

Low-volume alerting should be count-based instead of percentage-based.

Add alerts to:

```text
ops/observability/backend/prometheus/rules/backend.yml
```

Recommended alerts:

```text
warning: any 5xx response sustained over 5 minutes
critical: at least 5 5xx responses in 10 minutes
```

PromQL shape:

```promql
sum(increase(lantern_http_requests_total{status_code=~"5.."}[5m])) > 0
```

```promql
sum(increase(lantern_http_requests_total{status_code=~"5.."}[10m])) >= 5
```

Aggregate at alert level to avoid one alert per route. Route-level labels remain
available for debugging in Prometheus and Grafana.

### Worker Heartbeat

Promote the worker heartbeat from container-local healthcheck state to a
Prometheus textfile metric.

Current state:

- worker writes `SYNC_RUNNER_HEARTBEAT_PATH=/tmp/worker-heartbeat`
- Docker healthcheck reads that file inside the worker container

Plan:

- Mount the host textfile collector directory into the worker container.
- Point `SYNC_RUNNER_HEARTBEAT_PATH` at a `.prom` file in that mount, or add a
  separate `SYNC_RUNNER_HEARTBEAT_PROM_PATH`.
- Write heartbeat text atomically.
- Keep Docker healthcheck behavior intact.

Metric:

```text
lantern_sync_runner_last_heartbeat_timestamp_seconds
```

Use a Unix timestamp in seconds as the value.

### SyncJob Gauges

Collect aggregate SyncJob metrics from the backend `/metrics` endpoint. Keep
queries bounded and aggregate-only.

Metrics:

```text
lantern_sync_jobs_by_status{status}
lantern_sync_jobs_oldest_queued_age_seconds
lantern_sync_jobs_oldest_running_age_seconds
lantern_sync_jobs_due_queued_total
lantern_sync_jobs_last_dead_letter_timestamp_seconds
lantern_sync_jobs_metrics_collection_success
```

Failure behavior:

- `/metrics` should still return HTTP/process metrics if SyncJob DB collection
  fails.
- Set `lantern_sync_jobs_metrics_collection_success` to `0` on collection
  failure and `1` on success.
- Only update SyncJob gauges after successful DB collection, so a DB outage does
  not make the queue appear empty.

Do not label these metrics by User, Household, InstitutionConnection, Plaid
Item, or SyncJob ID.

### Worker And SyncJob Alerts

Tune alerts for low volume, where only a few sync jobs may happen per day.

Recommended alerts:

```text
critical: worker heartbeat stale for 2 minutes, held for 2 minutes
warning: SyncJob metrics collection failing for 5 minutes
warning: oldest queued SyncJob age > 1 hour for 10 minutes
critical: oldest running SyncJob age > 2 hours for 10 minutes
warning: dead-letter SyncJob activity within the last 24 hours
```

Use recent dead-letter activity rather than permanent dead-letter count to avoid
alerts that stay active forever.

## Files To Change

Backend:

- `backend/requirements.txt`
- `backend/src/server.py`
- `backend/src/infrastructure/metrics/__init__.py`
- `backend/src/infrastructure/metrics/http.py`
- `backend/src/infrastructure/metrics/sync_jobs.py`
- `backend/src/transactions_sync_runner.py`
- focused tests under `backend/tests/`

Deployment and observability:

- `ops/deployment/backend/app-stack/compose.yml`
- `ops/deployment/backend/app-stack/compose.env.example`
- `ops/observability/backend/prometheus/prometheus.yml`
- `ops/observability/backend/prometheus/rules/backend.yml`
- `ops/observability/backend/grafana/dashboards/lantern-overview.json`
- `ops/observability/backend/README.md`

Architecture record:

- `docs/adr/0019-app-native-observability-metrics.md`

## Verification

Automated verification is required:

- backend pytest coverage for HTTP middleware and `/metrics`
- backend pytest coverage for SyncJob aggregate collection success and failure
- backend pytest coverage for worker heartbeat textfile output
- Prometheus config and rules validation with `promtool` when available
- JSON validity check for the Grafana dashboard

Local Docker Compose verification is required before treating the slice as done:

1. Start the app stack.
2. Start the observability stack.
3. Confirm Prometheus target `backend` is up.
4. Query `lantern_http_requests_total`.
5. Trigger a controlled backend 500 and confirm the 5xx counter increases.
6. Confirm `lantern_sync_runner_last_heartbeat_timestamp_seconds` updates.
7. Confirm SyncJob gauges are present.
8. Confirm the Grafana overview dashboard renders the backend 5xx and p95
   latency panels.
9. Confirm `/metrics` is not available through nginx or any public route.

## Implementation Order

1. Add Prometheus client dependency.
2. Add metrics infrastructure modules and FastAPI `/metrics`.
3. Add isolated tests for HTTP metrics.
4. Add SyncJob aggregate gauges and tests.
5. Add worker heartbeat textfile metric and tests.
6. Wire production Compose mounts and env examples.
7. Add Prometheus scrape config and alerts.
8. Update Grafana dashboard.
9. Update observability README.
10. Run automated verification.
11. Run required local Docker Compose verification.
