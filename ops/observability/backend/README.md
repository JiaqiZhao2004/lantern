# Backend Observability

This component owns Slice 5: first-pass monitoring for the production backend host.

## Boundary

Slice 5 keeps observability separate from the backend app stack. Monitoring lives under
`ops/observability/backend/` with its own Compose/runbook surface and attaches to the
existing backend app stack instead of editing `ops/deployment/backend/app-stack/compose.yml`
as part of the app rollout path.

This keeps monitoring deployable and restartable on its own while still watching the same
host, containers, Postgres database, backend service, and backup posture.

## Initial Scope

- Prometheus
- Grafana
- metrics for the host
- metrics for backend app stack containers
- metrics for Postgres
- metrics or probes for backend availability
- backup freshness and failure alerting
- email delivery for the first alert channel

## Day-One Stack

- Prometheus
- Alertmanager
- Grafana
- `node_exporter` for host metrics and textfile collector backup markers
- `cadvisor` for container metrics
- `postgres_exporter` for Postgres metrics
- `blackbox_exporter` for HTTP probes

## Files

- [compose.yml](../../observability/backend/compose.yml)
- [observability.env.example](../../observability/backend/observability.env.example)
- [render-alertmanager-config.sh](../../observability/backend/render-alertmanager-config.sh)
- [prometheus/prometheus.yml](../../observability/backend/prometheus/prometheus.yml)
- [prometheus/rules/](../../observability/backend/prometheus/rules)
- [blackbox/blackbox.yml](../../observability/backend/blackbox/blackbox.yml)
- [grafana/provisioning/](../../observability/backend/grafana/provisioning)
- [grafana/dashboards/](../../observability/backend/grafana/dashboards)
- [postgres/create-monitoring-role.sh](../../observability/backend/postgres/create-monitoring-role.sh)
- [postgres/create-monitoring-role.sql](../../observability/backend/postgres/create-monitoring-role.sql)

## First-Time Setup

Run these steps from `ops/observability/backend/` on the backend host.

1. Create the shared backend Docker network if it does not already exist:

```bash
docker network inspect lantern-backend >/dev/null 2>&1 || docker network create lantern-backend
```

2. Create the real observability env file if it does not already exist:

```bash
test -f observability.env || cp observability.env.example observability.env
```

Fill in `observability.env`, including:

- Grafana admin password
- `DATA_SOURCE_NAME` for the dedicated `lantern_monitor` Postgres role
- SMTP settings for Alertmanager

3. Create or rotate the dedicated Postgres monitoring role:

```bash
./postgres/create-monitoring-role.sh
```

The helper reads the `lantern_monitor` password from `DATA_SOURCE_NAME` in
`observability.env` so the exporter connection string is the single source of truth.

4. Render the host-local Alertmanager config:

```bash
./render-alertmanager-config.sh
```

5. Create the node exporter textfile collector directory:

```bash
mkdir -p textfile_collector
```

Set `BACKUP_PROM_TEXTFILE_DIR` in `ops/durability/backend/backup.env` to the absolute
path for this directory, usually:

```bash
BACKUP_PROM_TEXTFILE_DIR=/srv/lantern/ops/observability/backend/textfile_collector
```

6. Start observability:

```bash
docker compose --env-file observability.env -f compose.yml up -d
```

7. Open the private UIs through an SSH tunnel from your workstation:

```bash
ssh -L 9090:127.0.0.1:9090 -L 9093:127.0.0.1:9093 -L 3001:127.0.0.1:3001 <host>
```

Then visit:

- Prometheus: `http://127.0.0.1:9090`
- Alertmanager: `http://127.0.0.1:9093`
- Grafana: `http://127.0.0.1:3001`

## Postgres Exporter Access

`postgres_exporter` should use a dedicated monitoring Postgres role, not the normal app
database credentials. The role should be read-only and limited to the permissions required
for exporter views and statistics.

The monitoring database password belongs in a host-side observability env file and must not
be committed to the repository.

Slice 5 includes a checked-in, rerunnable SQL/script path for creating or updating the
monitoring role. The helper reads the role password from the host-local
`DATA_SOURCE_NAME`; the password is never embedded in checked-in SQL.

## Grafana Provisioning

Slice 5 should provision baseline Grafana datasources and dashboards from repo-owned files
instead of relying on dashboards built manually in the Grafana UI.

Baseline dashboards should stay small:

- host health
- container health
- Postgres health
- backup freshness
- API availability

Manual dashboards can still be used for exploration, but replacement-host recovery should
not depend on unreproducible Grafana UI state.

## Runtime Integration

The observability stack should scrape backend app stack services over a shared named Docker
network. The backend app stack Compose file and the observability Compose file should agree
on one external network name so Prometheus can use stable container DNS names for backend,
nginx, db, and exporter targets.

The shared network should be host-owned, not owned by either Compose project:

- default name: `lantern-backend`
- env knob: `BACKEND_SHARED_NETWORK`
- host setup command: `docker network inspect lantern-backend >/dev/null 2>&1 || docker network create lantern-backend`
- app stack services attached: `nginx`, `backend`, `worker`, and `db`
- observability services attached: Prometheus, `blackbox_exporter`, and `postgres_exporter`

Because the network is external, `docker compose down` for either stack should not remove
the shared app/monitoring connectivity.

Slice 5 should update the app stack Compose file directly to join this network rather than
adding an optional observability override file. This keeps the production topology singular;
the bring-up docs must create the external network before starting the app stack.

Prometheus and Grafana UI ports should still bind only to loopback on the host.

## First-Cut Metrics

### Host

- CPU usage and load average
- memory and swap usage
- disk usage for `/`, Docker storage, and the backup directory
- disk I/O saturation or latency
- network throughput and errors
- host uptime and reboot detection
- systemd unit state for `cloudflared`, Docker, and backup timers

### Containers

- container up/down/restarting state for `nginx`, `backend`, `worker`, and `db`
- container CPU and memory usage
- restart counts
- Docker healthcheck status

### Backend Availability

- backend `/health/live` status
- backend `/health/ready` status through local `nginx`
- production same-origin API synthetic check through `lantern.royzhao.dev/api/*`, deferred
  until there is a safe non-human token strategy

### Worker

- worker container health
- worker heartbeat freshness
- stale queued or running SyncJobs

### Postgres

- Postgres up/down
- active connections versus max connections
- database size
- table sizes for core transaction data
- locks, deadlocks, and long-running queries

### Backups

- last successful backup timestamp
- last backup duration
- last backup size
- last S3 upload success timestamp
- backup failure count
- freshness for six-hourly backups
- freshness for weekly backups
- local backup directory size

Backup freshness should come from local Prometheus textfile collector marker files written
by `backup-db.sh`, with separate metrics for local dump success and S3 upload success.
Markers must be written only after the corresponding operation succeeds, via a temporary
file and atomic rename, so an interrupted or failed backup cannot produce a false healthy
signal.

Systemd/journald state and S3 object age are useful cross-checks, but they are not the
primary first-pass freshness signal.

### Monitoring System

- Prometheus target scrape failures
- Prometheus rule evaluation failures
- Prometheus storage disk usage
- Alertmanager up/down
- email alert delivery test procedure

## Alert Posture

Slice 5 uses a small severity model:

- `critical`: local backend readiness down, Postgres down, six-hour backup freshness missed
- `warning`: high disk usage, container restart loops, local readiness failing while
  production status is unknown, weekly backup freshness missed, Prometheus scrape failures
- `info`: explicit test alerts only

Alerts should include short debounce windows so routine deploys and service restarts do not
email immediately. Backend and Postgres availability alerts should wait about five minutes.
Backup freshness alerts should fire only after the expected interval plus a grace window.

Production-path alerting should wait until Lantern has a safe non-human credential for a
synthetic API request. Do not store a personal Firebase token or manually copied browser
credential in Prometheus or Alertmanager.

## Alert Delivery

Alertmanager should send first-pass alerts through generic SMTP.

Slice 5 should commit an `observability.env.example` with placeholder SMTP settings and
keep the real `observability.env` only on the backend host. SMTP usernames, passwords, app
passwords, or provider tokens must not be committed.

The runbook should include a test-alert step so email delivery is verified before relying
on alerts operationally.

## Deferred Metrics

- app-native `/metrics`
- route-level request rate, error rate, and latency percentiles
- app build/version info metrics
- detailed SyncJob counters by trigger, result, and upstream failure type
- log aggregation
- tracing

## Access Model

Prometheus and Grafana stay private in Slice 5. They should be bound to loopback or
reached through an SSH tunnel, not exposed through Cloudflare, CloudFront, or a public
admin hostname.

Public dashboard access is deferred until there is a deliberate admin-access design for
authentication, TLS, dashboard authorization, and secret handling.

## Out Of Scope

- app deployment changes beyond documented scrape/probe integration
- log aggregation
- tracing
- external managed observability
- multi-host or high-availability monitoring
