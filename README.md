# h-cam-2.0
mayank repo of h cam experiment

## Phase 0 foundation

Phase 0 defines the H-CAM product baseline, requirements, architecture,
governance, validation gates, and Phase 1 entry plan.

Start here: [docs/phase-0/README.md](docs/phase-0/README.md)

## Sentinel CCTV environment probe

This repository includes a safe, read-only probe for the Sentinel Gujarat CCTV
reference environment. It is for development planning and stream compatibility
checks only; it does not bulk-download CCTV footage.

```powershell
python tools/sentinel_cctv_probe.py metadata
python tools/sentinel_cctv_probe.py state --camera-id 1
python tools/sentinel_cctv_probe.py stream-test --camera-id 1
python tools/sentinel_cctv_probe.py snapshot
python tools/sentinel_cctv_probe.py offline-summary
python tools/sentinel_cctv_probe.py registry-export --output fixtures/sentinel/registry-seed.json
python tools/sentinel_cctv_probe.py all
```

Default target: `https://live.sentinelgujarat.in`

Offline regression checks:

```powershell
python -m py_compile tools/sentinel_cctv_probe.py
python -m unittest discover -s tests -v
```

See [docs/phase-0/cctv-environment.md](docs/phase-0/cctv-environment.md) for
the observed API shape, safety rules, and test workflow.
