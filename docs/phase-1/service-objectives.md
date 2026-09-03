# Phase 1 Service Objectives And Metrics

Phase 1 now produces bounded operational telemetry for the camera-registry
foundation. These objectives are engineering regression gates, not a police
operations SLA, city-scale capacity claim, or production deployment approval.

## Telemetry Contract

Set both values to enable the endpoint:

```text
HCAM_METRICS_ENABLED=true
HCAM_METRICS_TOKEN_FILE=/run/secrets/metrics_token
```

`GET /internal/metrics` requires `Authorization: Bearer <token>`. The token must
be 32 to 256 bearer-safe characters and is read from a UTF-8 single-value file.
It is excluded from settings representations, responses, logs, metric labels,
and build artifacts. Disabled metrics return `404`; missing or incorrect
credentials return `401`.

The Prometheus exposition contains:

- `hcam_http_requests_total{method,route,status_class}`;
- `hcam_http_request_duration_seconds{method,route}`;
- `hcam_service_info{service,version}`.

`route` is the bounded FastAPI route template, such as
`/cameras/{camera_id}`, or `<unmatched>`. Camera IDs, query strings, actor IDs,
departments, request bodies, stream references, client addresses, credentials,
and exception text are never labels. This avoids sensitive telemetry and
unbounded label cardinality.

## CI Regression Objectives

| Indicator | Automated objective | Evidence |
| --- | --- | --- |
| Sequential registry latency | list and detail p95 at or below 750 ms | `tools/phase1_performance.py` |
| Concurrent loopback latency | aggregate p95 at or below 1,500 ms | `tools/phase1_load.py` |
| Concurrent request errors | zero errors in 400 requests at concurrency 16 | `tools/phase1_load.py` |
| Synthetic import time | 1,000 records within 20 seconds | `tools/phase1_performance.py` |
| SQLite recovery time | backup, verify, restore, and readiness within 60 seconds | `hcam recovery-drill` |
| Schema readiness | exact migration and required-column checks pass | `/health/ready` |

The thresholds detect severe regressions on shared CI runners. They do not
model network cameras, concurrent writes, production PostgreSQL tuning,
multi-node failover, police workflows, or 80,000-camera capacity.

## Proposed Staging SLOs

Before production planning, an approved staging environment should establish
realistic windows and error budgets for:

- registry API successful-request ratio;
- registry read p95 and p99 latency;
- readiness success ratio;
- import success ratio and duration;
- database connection saturation;
- backup age and restore-drill success;
- alerting delivery and operator acknowledgement.

Targets must be approved against deployment topology, hardware, workload,
identity, and support coverage. Phase 1 intentionally does not invent a
production availability percentage without that evidence.

## Dashboard

The version-controlled Grafana dashboard at
`deploy/observability/hcam-phase1-overview.json` visualizes request rate, HTTP
5xx ratio, registry p95 latency, readiness success, and response classes. Its
Prometheus data source is selected through a dashboard variable rather than a
hard-coded environment.

Metrics still require transport security, network restriction, secret
rotation, scrape authorization, retention policy, and monitoring ownership in
an approved deployment. The Phase 1 bearer token protects only this internal
scrape endpoint and is not a user or police identity provider.
