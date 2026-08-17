# h-cam-2.0
mayank repo of h cam experiment

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
