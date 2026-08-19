# Safety and Data Governance

## Allowed

- generated color/test-pattern video;
- local loopback and private Compose networking;
- explicit 50-stream scale tests;
- metadata-only FFprobe checks;
- one explicit ONVIF simulator;
- read-only capability queries against its configured media-service URL;
- authenticated HLS manifest checks;
- synthetic camera and audit records.

## Prohibited in Phase 2

- real cameras or CCTV feeds;
- real-person footage of any kind;
- LAN or internet camera discovery, host enumeration, or WS-Discovery;
- production Sentinel/Government endpoints in the lab;
- Government databases or identity records;
- bulk video download, recording, evidence retention, or frame export;
- face recognition, person identification, watchlists, biometrics, or AI event
  analytics;
- bypassing stream authentication or broadening the network allowlist with a
  wildcard;
- using environment proxies, redirects, or implicit hostname DNS to escape the
  adapter egress boundary;
- representing synthetic results as deployment approval.

The Sentinel adapter remains a separate, read-only Phase 0 reference utility.
It is not invoked by the Phase 2 lab or CI.

## Production Gates Still Required

Real deployment requires written authority, DPIA/legal review, approved
purpose limitation, camera/network inventory, production identity and secret
management, TLS/VPN design, retention schedules, evidence controls, operator
training, incident response, model governance where applicable, and measured
capacity on approved infrastructure.
