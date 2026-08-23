# Data Governance

H-CAM deals with sensitive public-safety data. Phase 0 must set conservative
rules before the platform touches official datasets, watchlists, biometrics, or
production CCTV.

## Data Classes

| Class | Examples | Phase 0 Rule |
| --- | --- | --- |
| Public reference metadata | Sentinel camera metadata, stream state fields | Allowed for safe read-only testing |
| Local development fixtures | `fixtures/sentinel/*.json` metadata/state snapshots | Allowed, ignored by Git, no video |
| CCTV footage | raw video, clips, frames, snapshots | Do not bulk download in Phase 0 |
| Derived media metadata | codec, container, stream reachability, duration | Allowed through metadata-only probes |
| PII | faces, people attributes, vehicle ownership, phone numbers | Not allowed without authorization and policy |
| Sensitive police data | watchlists, FIR/case data, government databases | Not allowed without formal data contracts |
| Audit/security data | access logs, exports, policy changes | Required before sensitive workflows |

## Safety Rules

- Use read-only public endpoints only.
- Do not bypass authentication, access controls, or hidden endpoints.
- Do not scrape or bulk-download CCTV video.
- Do not store real video in Git, fixtures, issue comments, PRs, or docs.
- Do not add biometric recognition or government database matching until legal
  authorization, retention policy, audit, and human review workflows exist.
- Treat all external system data as externally owned, not H-CAM-owned.

## Access Model

Future product implementation must support:

- least-privilege access
- role-based permissions
- per-camera and per-case access boundaries
- approval workflows for sensitive exports
- emergency access with mandatory audit
- service credentials stored as secrets, never in source control

## Retention Model

Phase 0 retention:

- generated JSON fixtures stay local and ignored by Git
- no video retention
- no official data retention

Future retention policy must define:

- raw video retention duration
- derived metadata retention duration
- audit log retention duration
- evidence retention duration
- deletion and legal hold behavior
- export approval and chain of custody rules

## Audit Requirements

The platform must eventually audit:

- login and failed login events
- camera reads and stream access
- case/evidence reads
- search queries involving people, vehicles, plates, or watchlists
- exports/downloads
- policy and role changes
- model/watchlist changes
- admin override actions

## Human Review

AI output must support human review. Alerts and matches should include model
confidence, evidence links, source camera, timestamp, and reason. The system
must avoid presenting probabilistic AI output as unquestionable fact.
