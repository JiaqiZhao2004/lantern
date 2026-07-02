# App-Native Observability Metrics

Lantern will expose app-native metrics through the existing self-hosted
observability stack. The FastAPI backend will serve `/metrics` only on the
private backend Docker network, and Prometheus will scrape it directly at
`backend:8000/metrics`. The route will not be exposed through nginx, Cloudflare,
CloudFront, or any public API path.

Backend HTTP instrumentation will record request count, latency, in-progress
requests, and 5xx responses using bounded labels: method, FastAPI route
template, and status code. `/metrics`, `/health/live`, and `/health/ready` are
excluded from these request metrics. Health remains monitored by the existing
blackbox probes so routine health traffic does not dilute low-volume API error
signals.

The transaction sync worker will emit its heartbeat through the existing
node_exporter textfile collector rather than running its own HTTP metrics
server. Aggregate SyncJob state will be collected by the backend `/metrics`
endpoint with bounded database queries over `sync_jobs`. SyncJob metrics will
include counts by status, oldest queued/running age, due queued count, last
dead-letter timestamp, succeeded-job count, last succeeded-job age, and
collection success. If SyncJob collection fails,
`/metrics` will still return other metrics and mark SyncJob collection as
unsuccessful rather than making the queue appear empty.

We chose this topology because Lantern already runs Prometheus, Alertmanager,
Grafana, node_exporter, cAdvisor, postgres_exporter, and blackbox_exporter as a
separate observability stack attached to the shared backend Docker network.
Direct private scraping keeps operational metrics off the public ingress path.
Using textfile collector for the worker heartbeat avoids adding a long-running
HTTP server to the worker. Collecting aggregate SyncJob gauges through the
backend avoids a dedicated exporter process until the domain needs richer worker
event metrics.

Alternatives considered:

- expose `/metrics` through nginx, rejected to reduce accidental public exposure
  during future edge-routing changes
- add a worker HTTP metrics server, rejected because the first worker metric is
  heartbeat freshness and textfile collector already exists
- add a dedicated SyncJob exporter, rejected as extra runtime surface for simple
  aggregate database gauges
- alert only through cAdvisor container health, rejected because heartbeat and
  queue age are app concepts, not just container concepts

The first alert set is tuned for low traffic. HTTP 5xx critical alerting uses
counts over time rather than percentages. Worker alerts focus on stale
heartbeat, failed SyncJob metric collection, old queued jobs, old running jobs,
stale succeeded-job freshness, and recent dead-letter activity.
