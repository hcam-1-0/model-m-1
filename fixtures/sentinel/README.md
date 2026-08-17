# Sentinel Fixtures

This directory is the default output location for generated Sentinel CCTV JSON
fixtures.

Generate fixtures with:

```powershell
python tools/sentinel_cctv_probe.py snapshot
```

The snapshot command stores camera metadata and selected camera state JSON only.
It must not store CCTV footage.
