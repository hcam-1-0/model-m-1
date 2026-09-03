# Phase 2.5: Controlled Camera Lab And Test Feeds

Status: online Sentinel catalogue and one-camera zero-retention playback are
implemented and validated locally. The multi-camera external ramp remains
closed.

Phase 3 work is paused. Phase 2.5 now provides a controlled compatibility lab
for the public Sentinel sandbox at `live.corp8.cloud`, plus the existing
generated environment as an offline fallback. The current authority is limited
to read-only catalogue retrieval and bounded live preview with zero retention.
It does not authorize authenticated/private access, camera control, recording,
downloads, analytics, Government/private data, or deployment.

## Current Notes

- [Phase 2.5 master plan](plan.md)
- [Lab topology and test matrix](lab-topology-and-test-matrix.md)
- [`sentinel_sandbox_catalog_v1` adapter contract](catalog-adapter-contract.md)
- [Security and validation gates](security-and-validation-gates.md)
- [Backlog and owner decisions](backlog-and-owner-decisions.md)
- [Official Sentinel sandbox integrator-guide notes](official-sentinel-sandbox-notes.md)
- [`live.corp8.cloud` public environment notes](live-corp8-public-environment-notes.md)
- [Sentinel lab implementation](implementation.md)
- [Three-adapter architecture](three-adapter-architecture.md)
- [Teammate laptop and GPU runbook](teammate-laptop-runbook.md)
- [Phase 3 media/timestamp handoff](phase3-media-timestamp-handoff.md)

## Implemented Direction

The separately versioned Sentinel sandbox adapter consumes the public
`https://live.corp8.cloud/api/ingest` catalogue and normalizes its advertised
RTSP, WHEP, and HLS metadata. It does not modify or replace the Phase 0
`sentinel_reference_v1` adapter or the future main product adapter.

The test dashboard exposes two resource profiles over the same live catalogue:

- `lab1highadapter`: 50-slot holder, current 30-camera inventory, 30-connection
  ceiling, four concurrent preview sessions, native source quality;
- `lab2lowadapter`: the same current 30-camera inventory, four-connection
  ceiling, one concurrent preview session, native source quality.

The public catalogue currently advertises 30 live cameras. The dashboard opens
one selected feed at a time. Browser playback uses the advertised HLS source as
an ephemeral FFmpeg stream-copy relay into a dedicated loopback WHEP gateway;
the relay writes no media files and is renewed through short leases. Direct
RTSP/WHEP remains available in the adapter contract but was not reachable from
this laptop during validation.

The previous 50 unique generated fixtures, simulator, fault cases, and GPU
preparation paths remain available behind the explicit `generated-fallback`
Compose profile. They are not the default online dashboard source.

## Working Boundary

- Treat the public Sentinel environment as a sandbox reference, not production
  CCTV or proof of deployment conformance.
- Keep the older public `live.sentinelgujarat.in` reference adapter isolated.
- Use only exact transport locations returned by the current catalogue; never
  synthesize per-camera URLs.
- Keep redirects and environment proxies disabled and validate every outbound
  scheme, host, port, path, and resolved address.
- Keep recording, download, screenshot/frame export, analytics, and Government
  data paths disabled.
- Require new authorization before credentials, private hosts, multiple
  simultaneous external feeds, or any deployment use.

## Current Sequence

1. run the online catalogue verification and one-camera browser smoke;
2. verify high/low profile switching against the same 30-camera inventory;
3. retain G8 multi-camera external scale as closed;
4. use generated fallback only for offline fault, scale, and GPU testing; and
5. require owner acceptance of an exact package digest before Phase 2.5 is
   treated as accepted history.
