# Safety and Data Governance

## Allowed

- generated color/test-pattern video;
- local loopback and private Compose networking;
- explicit 50-stream scale tests;
- metadata-only FFprobe checks;
- one explicit ONVIF simulator;
- read-only capability queries against its configured media-service URL;
- read-only synthetic imaging inspection and bounded synthetic event pulls;
- synthetic PTZ commands with explicit global/per-stream gates, a dedicated
  controller role, per-stream leases, velocity/duration limits, and auto-stop;
- administrator-triggered WS-Discovery on one explicitly configured isolated
  lab interface and exact private CIDRs, returning metadata only;
- authenticated metadata-only validation of one owned and authorized isolated
  private camera when the private-lab gate is explicitly enabled;
- authenticated HLS manifest checks;
- synthetic camera and audit records.

## Prohibited in Phase 2

- real cameras or CCTV feeds;
- real-person footage of any kind;
- internet camera discovery, arbitrary LAN scans, host enumeration, wildcard
  discovery, or discovery outside the exact configured private CIDRs;
- production Sentinel/Government endpoints in the lab;
- Government databases or identity records;
- bulk video download, recording, evidence retention, or frame export;
- image capture, recording, provisioning, configuration writes, firmware
  operations, or PTZ movement on a physical camera without separate written
  authorization and a dedicated validation procedure;
- face recognition, person identification, watchlists, biometrics, or AI event
  analytics;
- bypassing stream authentication or broadening the network allowlist with a
  wildcard;
- using environment proxies, redirects, or implicit hostname DNS to escape the
  adapter egress boundary;
- representing synthetic results as deployment approval.
- claiming ONVIF conformance without completing ONVIF's formal process for the
  exact release.

The Sentinel adapter remains a separate, read-only Phase 0 reference utility.
It is not invoked by the Phase 2 lab or CI.

## Production Gates Still Required

Real deployment requires written authority, DPIA/legal review, approved
purpose limitation, camera/network inventory, production identity and secret
management, TLS/VPN design, retention schedules, evidence controls, operator
training, incident response, model governance where applicable, and measured
capacity on approved infrastructure.

Authenticated production use additionally requires an approved external secret
provider and enforced network egress controls. The development file provider
and HTTP lab exception are both forbidden in production.
