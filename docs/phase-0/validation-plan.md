# Validation Plan

Phase 0 validation proves the project foundation is usable, safe, and testable
before moving into product implementation.

## Validation Categories

| Category | Command Or Evidence | Purpose |
| --- | --- | --- |
| Python compile | `python -m py_compile tools/sentinel_cctv_probe.py tools/phase0_readiness.py` | Catch syntax/runtime import issues |
| Unit tests | `python -m unittest discover -s tests -v` | Verify deterministic logic and docs structure |
| Phase 0 readiness | `python tools/phase0_readiness.py --run-validation` | Confirm automated gates and list manual owner/official gates |
| Live metadata | `python tools/sentinel_cctv_probe.py metadata --json` | Confirm Sentinel metadata endpoint shape |
| Live state | `python tools/sentinel_cctv_probe.py state --camera-id 1` | Confirm selected camera state shape |
| Stream metadata | `python tools/sentinel_cctv_probe.py stream-test --camera-id 1` | Confirm metadata-only stream probing works |
| Snapshot | `python tools/sentinel_cctv_probe.py snapshot` | Confirm local metadata/state fixture creation |
| Offline summary | `python tools/sentinel_cctv_probe.py offline-summary` | Confirm fixture reuse without network |
| Registry seed | `python tools/sentinel_cctv_probe.py registry-export` | Confirm normalized H-CAM camera registry export |
| CI | GitHub Actions `Python CI` | Confirm checks pass outside the laptop |

## Required Evidence Before Phase 1

- CI is green on `main`.
- Sentinel probe commands produce clear output and do not store video.
- Stream failures are reported as data, not unhandled crashes.
- Registry export produces `hcam.camera_registry.seed.v1`.
- Phase 0 docs are present and linked.
- Data governance constraints are documented.
- Phase 0 readiness reports `complete` after the project owner approves every
  manual gate.

## Live-Site Caveat

Live Sentinel behavior can change. Live checks prove current reachability only.
Offline tests and fixtures prove deterministic behavior independent of the live
site.
