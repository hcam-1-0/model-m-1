# Controlled ONVIF Operations

## Scope

Phase 2 implements a deliberately narrow ONVIF management surface:

- Media `GetProfiles` resolves profile, video-source, and PTZ configuration.
- Imaging `GetImagingSettings` reads current metadata only.
- Events creates one pull-point subscription, requests at most 32 messages for
  at most five seconds, and attempts `Unsubscribe` in all cases.
- PTZ supports stop, continuous, relative, absolute, and go-to-preset against
  the deterministic simulator. Continuous movement always issues stop.
- WS-Discovery sends one NetworkVideoTransmitter probe from one exact interface
  and returns only approved private literal-IPv4 XAddrs. It does not contact
  any discovered address.

Image capture, recording, imaging writes, presets writes, provisioning,
firmware, reboot, and factory reset are not implemented.

## Authorization

Imaging inspection and event pulls require `camera.editor`, department scope,
and `X-HCAM-Reason`. PTZ requires `camera.controller` or `platform.admin` plus:

1. `HCAM_ONVIF_CONTROL_ENABLED=true` outside production.
2. `onvif_control_enabled=true` on the exact stream, set only by an admin.
3. Exact ONVIF egress authorization and verified TLS, or the explicit lab HTTP
   exception.
4. Per-stream velocity and duration limits.
5. One active movement lease per stream.

Stop remains available without acquiring a movement lease, but still requires
all authorization and control gates. WS-Discovery requires `platform.admin`,
`HCAM_ONVIF_DISCOVERY_ENABLED=true`, one exact private interface, and one or
more strict private IPv4 CIDRs. Production settings reject both control and
discovery flags.

## Data and Audit

`onvif_operation_runs` records the operation type, actor, safe parameters,
reason, outcome, bounded reason code, request ID, and duration. It never stores
credentials, secret references, locators, raw SOAP, frames, or event payloads.
`onvif_control_leases` prevents concurrent movement and expires after a bounded
interval. Prometheus labels use only operation type and outcome.

Every operation, including WS-Discovery and deprecated synchronous capability
discovery, commits a `pending` operation row and a requested audit event before
the network callback can execute. Completion atomically changes the row to
`success` or `failure` and writes a terminal audit event. Synchronous capability
success also stores its snapshot in that terminal transaction. If requested
intent cannot be persisted, no network action occurs. If completion persistence
fails, the original pending row remains for alerting and operator review rather
than presenting the action as unaudited success.

## Environment

```powershell
$env:HCAM_ONVIF_CONTROL_ENABLED = "true"
$env:HCAM_ONVIF_DISCOVERY_ENABLED = "true"
$env:HCAM_ONVIF_DISCOVERY_INTERFACE = "10.20.30.5"
$env:HCAM_ONVIF_DISCOVERY_ALLOWED_NETWORKS = "10.20.30.0/24"
$env:HCAM_ONVIF_DISCOVERY_TIMEOUT_SECONDS = "2"
$env:HCAM_ONVIF_DISCOVERY_MAX_RESULTS = "32"
```

These settings authorize only the application path. Host firewall, VLAN, and
production egress controls remain mandatory external boundaries. H-CAM must not
claim ONVIF conformance unless an exact release completes ONVIF's formal
conformance process.
