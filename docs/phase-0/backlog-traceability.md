# Phase 0 Backlog Traceability

Status: accepted baseline with maintenance review only.

Phase 0 is not reopened for new product features. Its ongoing backlog protects
the requirements, source provenance, safety rules, and reference adapter that
later phases depend on.

| Work item | State | Authoritative evidence | Maintenance action |
| --- | --- | --- | --- |
| P0-01 Product and requirements baseline | Complete | `product-brief.md`, `requirements.md` | Review when official scope changes |
| P0-02 Architecture and module boundaries | Complete | `architecture-baseline.md` | Reject later boundary drift |
| P0-03 Data governance and safety | Complete | `data-governance.md` | Re-review before any sensitive data use |
| P0-04 Sentinel metadata adapter | Complete | `tools/sentinel_cctv_probe.py` | Keep read-only and metadata-only |
| P0-05 Offline fixtures and summary | Complete | ignored fixtures, probe tests | Update only for documented schema drift |
| P0-06 Registry seed export | Complete | `hcam.camera_registry.seed.v1` tests | Preserve backward compatibility |
| P0-07 Validation and CI | Complete | `tools/phase0_readiness.py`, CI | Run on every cross-phase release |
| P0-08 Official constraints intake | Accepted baseline | `official-constraints-intake.md` | Reverify from official sources before submission or sensitive integration |
| P0-09 Owner gates | Closed | issues #10 through #13 | Open a new gate instead of rewriting history |
| P0-10 Phase 1 handoff/backlog | Delivered | `phase-1-handoff.md`, `phase-1-backlog.md` | Trace through Phase 1 evidence |

## Review Gate

Phase 0 remains current when strict readiness passes, generated fixture paths
remain ignored, no committed media exists, the Sentinel adapter performs no
authentication bypass or endpoint scanning, and all requirement changes have a
source and decision record.

## Deferred By Design

Official credentials, Government databases, real CCTV media, biometrics,
watchlists, evidence retention, and production authorization are not Phase 0
backlog items. They require separate legal, security, data, and owner gates.
