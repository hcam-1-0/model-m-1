# H-CAM Teammate Setup

The `main` branch is a self-contained integration workspace for the H-CAM team. It
contains the completed Phase 3 analytics foundation and the separate Phase 2.5
Sentinel lab dashboard. It is intended for development and testing by team
members, not for production deployment.

## Included Components

- Phase 3 generated-only detection, per-camera tracking, geometry events,
  synthetic ANPR, runtime profiles, contracts, evidence, and validation tools.
- `lab1highadapter` for higher-resource laptops: 50 catalogue slots, up to 30
  managed connections, and up to four concurrent previews.
- `lab2lowadapter` for lower-resource laptops: the same catalogue and native
  media quality, with four managed connections and one preview.
- One shared loopback-only test dashboard for selecting either lab adapter.

The Phase 2.5 adapters are compatibility-lab components. They do not activate
Phase 3 analytics and do not replace the future H-CAM product camera adapter.

## Prerequisites

- Git
- Python 3.12
- `uv` 0.12.3
- FFmpeg and `ffprobe`
- Docker Desktop for the container-based lab path

A GPU is optional. The lab doctor detects available acceleration and reports a
compatible choice. The low adapter remains available when CPU, memory, or GPU
capacity is limited.

## Clone And Install

```powershell
git clone https://github.com/hcam-1-0/model-m-1.git
Set-Location model-m-1
git switch main
uv sync --locked --extra dev --extra analytics
```

Do not place credentials in the repository or command history. The default lab
path does not require camera credentials.

## Verify The Checkout

Run the lab checks before starting services:

```powershell
uv run --locked --extra dev python tools/phase2_5_lab.py doctor --host-only --accelerator auto
uv run --locked --extra dev pytest -q tests/test_phase2_5_adapter.py tests/test_phase2_5_apps.py tests/test_phase2_5_catalog.py tests/test_phase2_5_dashboard_safety.py tests/test_phase2_5_deployment.py tests/test_phase2_5_evidence.py tests/test_phase2_5_lab_adapters.py tests/test_phase2_5_media.py tests/test_phase2_5_runtime_boundaries.py tests/test_phase2_5_runtime_lifecycle.py tests/test_phase2_5_sentinel_online.py tests/test_phase2_5_standby.py tests/test_phase2_5_timing_faults.py tests/test_phase2_5_transports.py
uv run --locked --extra dev python tools/phase3_readiness.py --json
```

The online Sentinel test is opt-in and should remain disabled during routine
offline validation.

## Start The Lab Dashboard

Start Docker Desktop, then run:

```powershell
uv run --locked --extra dev python tools/phase2_5_lab.py start
uv run --locked --extra dev python tools/phase2_5_lab.py verify
```

Open `http://127.0.0.1:8091`. Use the dashboard controls to switch between
`lab1highadapter` and `lab2lowadapter`. The selected profile is persisted and
the service reconciles its bounded connection set.

Stop the lab when testing is complete:

```powershell
uv run --locked --extra dev python tools/phase2_5_lab.py stop
```

## Safety Boundaries

The lab is read-only and metadata/preview focused. Recording, bulk download,
frame export, camera control, private endpoints, Government data, and Phase 3
analytics activation remain disabled. The dashboard binds to loopback and is
not the future H-CAM operator dashboard.

## Detailed References

- [Phase 2.5 overview](docs/phase-2-5/README.md)
- [Laptop runbook](docs/phase-2-5/teammate-laptop-runbook.md)
- [Three-adapter architecture](docs/phase-2-5/three-adapter-architecture.md)
- [Phase 3 overview](docs/phase-3/README.md)
- [Phase 3 acceptance checklist](docs/phase-3/acceptance-checklist.md)
