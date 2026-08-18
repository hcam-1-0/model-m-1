# Operations and Observability

## Metrics

The protected `/internal/metrics` endpoint retains Phase 1 request metrics and
adds bounded-label gauges:

- `hcam_stream_health_state_total{state}`;
- `hcam_stream_probe_due_total`;
- `hcam_stream_outbox_unpublished_total`.

Metrics never label camera IDs, stream IDs, locators, actor IDs, tokens, or
Government identifiers. MediaMTX metrics and control API stay internal in the
lab.

Import `deploy/observability/hcam-phase2-streams.json` into Grafana for the
bounded fleet-state, probe-queue, outbox, request-rate, and p95-latency views.
Prometheus-compatible alert rules are provided in
`deploy/observability/hcam-phase2-alerts.yml`. The lab does not deploy or route
alerts automatically; an operator must configure an approved metrics backend
and notification policy.

The lab dispatcher drains health events to a metadata-only logging sink. A
nonzero unpublished gauge can be transient; a sustained backlog indicates sink
or dispatcher failure. Production must replace the validation sink with an
approved event bus that deduplicates on `event_id`.

## Logs

Worker events contain stream ID, worker ID, outcome, and normalized reason.
They do not include locators, bearer tokens, raw FFprobe output, frames, or
secret values. Container logs use bounded local rotation.

## Runbooks

### Worker runtime failure

1. Check worker heartbeat and container status.
2. Confirm `ffprobe -version` inside the image.
3. Verify database readiness and expired leases.
4. Verify the exact destination allowlist and mounted probe token.
5. Restart one worker; do not clear health history or leases manually unless
   an approved incident procedure requires it.

### Stream offline

1. Review current state, reason code, counters, and recent probes.
2. Confirm the endpoint is an authorized synthetic or approved destination.
3. Queue one immediate probe with a reason.
4. Do not bypass authentication or network policy to make a probe pass.

### Media gateway

1. Check internal MediaMTX API/metrics and publisher readiness.
2. Confirm recording remains disabled.
3. Confirm JWKS issuer/audience and key ID match.
4. Test a bounded manifest with a newly issued token.
5. Test anonymous and cross-stream denial.

### Data cleanup

Probe runs expire after seven days. Playback session records contain metadata
and JTI hashes only. The lab stop command removes its disposable PostgreSQL
volume; generated secrets can then be deleted through the normal filesystem
workflow.
