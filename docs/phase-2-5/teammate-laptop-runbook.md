# Phase 2.5 Teammate Laptop Runbook

<!-- markdownlint-disable MD013 -->

Status: public Sentinel sandbox catalogue and bounded one-camera preview are the
default; generated media is an optional offline fallback.

## Supported Shape

The lab is portable across teammate laptops with Python 3.12+, FFmpeg/FFprobe,
Docker Compose, and HTTPS access to `live.corp8.cloud`. Online previews use
native stream-copy and do not require a GPU. GPU acceleration is optional and
used only to prepare the generated fallback fixtures.

Supported acceleration choices:

| Host | Recommended mode | Notes |
| --- | --- | --- |
| Any CPU | `--accelerator cpu` | Slowest preparation, most portable |
| Automatic | `--accelerator auto` | Probes actual H.264 and HEVC encode ability before selection |
| NVIDIA Windows/Linux | `--accelerator nvidia` | Uses NVENC when smoke test succeeds, otherwise per-codec CPU fallback |
| Intel Windows | `--accelerator intel` | Uses Quick Sync when available |
| AMD Windows | `--accelerator amd` | Uses AMF when available |
| Intel/AMD Linux | `--accelerator vaapi` | Requires `/dev/dri`; use the VAAPI Compose overlay only on Linux |

## Prerequisites

1. Clone the branch and install the locked development environment.
2. Install FFmpeg with `ffmpeg` and `ffprobe` on `PATH`.
3. Start Docker Desktop or Docker Engine before `config`, `start`, or `all`.
4. Choose a local disk with at least 512 MiB free. Avoid cloud-mounted or
   sync-drive paths for SQLite and active media.
5. On Windows, share the selected drive with Docker Desktop when required.

```powershell
uv sync --locked --extra dev
uv run --locked --extra dev python tools/phase2_5_lab.py --help
```

## Storage Selection

Use any local folder outside the Git checkout. On Mayank's laptop, use F drive:

```powershell
$env:HCAM_PHASE2_5_STATE_ROOT = 'F:\h cam\runtime-storage\phase2-5'
New-Item -ItemType Directory -Force $env:HCAM_PHASE2_5_STATE_ROOT | Out-Null
```

Do not use `B:` on Mayank's laptop because it is a RaiDrive/Google Drive mount.
Teammates should choose their own local SSD path; the drive letter itself is
not part of the application contract.

The state root contains:

```text
phase2-5/
  catalog.db
  sentinel-online-catalog.db          online metadata/state only
  active-lab-adapter.json
  generated-media-manifest.json
  media/                         disposable generated MP4 files
  evidence/                      sanitized metadata and hashes only
  fault-request.json             short-lived generated fault request
  publisher-fault-status.json
  proxy-fault-status.json
```

## Preflight

Run host-only preflight first. It detects the OS, CPU count, free disk, ports,
FFmpeg version, listed hardware encoders, and real encoder smoke-test results.

```powershell
uv run --locked --extra dev python tools/phase2_5_lab.py doctor --host-only --accelerator auto --state-root $env:HCAM_PHASE2_5_STATE_ROOT
```

The dashboard binds to `127.0.0.1:8091`. Its dedicated Sentinel WHEP gateway
binds HTTP to `127.0.0.1:8890`, ICE UDP to `127.0.0.1:8191`, and ICE TCP to
`127.0.0.1:8192`. The older generated fallback retains ports 8889/8189/8190.
Change host ports through documented environment variables when a local
conflict exists; do not expose them on a LAN interface.

Do not select a GPU mode merely because FFmpeg lists its encoder. The runner
uses it only after a real H.264/HEVC smoke test. Each codec can fall back to CPU
independently.

Generated H.264 fixtures are encoded without B-frames and verified by FFprobe
before publication so MediaMTX can relay them through WHEP. A
`fixture_h264_b_frames_present` failure means the selected encoder ignored the
required browser-compatibility setting; choose another validated accelerator
or CPU. HEVC fixtures remain valid for RTSP and adapter compatibility tests,
but their Preview action is intentionally disabled in the browser dashboard.

## Recommended Online Sentinel Flow

This is the default flow on Windows and mixed teammate hardware. It does not
prepare or publish generated media:

```powershell
uv run --locked --extra dev python tools/phase2_5_lab.py config --container-gpu none --state-root $env:HCAM_PHASE2_5_STATE_ROOT
uv run --locked --extra dev python tools/phase2_5_lab.py start --skip-media-prepare --container-gpu none --state-root $env:HCAM_PHASE2_5_STATE_ROOT
uv run --locked --extra dev python tools/phase2_5_lab.py verify --state-root $env:HCAM_PHASE2_5_STATE_ROOT
```

Open the test dashboard at `http://127.0.0.1:8091`. This is not the future
H-CAM product dashboard.

The dashboard defaults to `Lab 1 High`. Both buttons show the same current
Sentinel inventory, which contained 30 cameras during validation. High permits
30 managed connections/four previews; `Lab 2 Low` permits four connections/one
preview. Low mode does not hide records or reduce camera quality.

The dashboard automatically selects a browser-compatible H.264 feed, preferring
a smaller native geometry to reduce startup cost. Select `View live` on another
camera to switch, or `Stop` to delete the short-lived relay and close the peer.
The browser renews the 60-second lease before expiry. Video is stream-copied,
not transcoded, downloaded, recorded, or retained.

## Generated Fallback Flow

Use this only for offline fault, 50-fixture, or GPU preparation tests:

```powershell
uv run --locked --extra dev python tools/phase2_5_lab.py prepare-media --accelerator auto --parallelism 4 --fixture-duration 2 --state-root $env:HCAM_PHASE2_5_STATE_ROOT
uv run --locked --extra dev python tools/phase2_5_lab.py start --skip-media-prepare --prepare-generated-fallback --container-gpu none --state-root $env:HCAM_PHASE2_5_STATE_ROOT
```

Generated high remains 50 records/30 publishers. Generated low remains 12
records/four publishers and reuses the same fixture quality.

## NVIDIA Container Option

Use this only when Docker can expose the NVIDIA GPU to Linux containers:

```powershell
uv run --locked --extra dev python tools/phase2_5_lab.py config --container-gpu nvidia --state-root $env:HCAM_PHASE2_5_STATE_ROOT
uv run --locked --extra dev python tools/phase2_5_lab.py start --container-gpu nvidia --accelerator nvidia --state-root $env:HCAM_PHASE2_5_STATE_ROOT
```

The overlay requests `gpus: all` and sets the generated publisher to NVIDIA. If GPU
pass-through is unavailable, use host preparation or CPU; do not weaken codec,
geometry, or timing assertions.

## Linux VAAPI Container Option

```bash
export HCAM_PHASE2_5_STATE_ROOT="$HOME/hcam-runtime/phase2-5"
uv run --locked --extra dev python tools/phase2_5_lab.py config --container-gpu vaapi --state-root "$HCAM_PHASE2_5_STATE_ROOT"
uv run --locked --extra dev python tools/phase2_5_lab.py start --container-gpu vaapi --accelerator vaapi --state-root "$HCAM_PHASE2_5_STATE_ROOT"
```

The overlay mounts `/dev/dri` and selects VAAPI. The configured render group
must match the host. This option is not intended for Docker Desktop on Windows.

## Fault Validation

Faults are generated-only, one camera at a time, and expire within 30 seconds.
The exact scenarios are `F1` through `F7`.

```powershell
uv run --locked --extra dev python tools/phase2_5_lab.py fault --scenario F4 --confirm-generated-only --fault-duration 10 --state-root $env:HCAM_PHASE2_5_STATE_ROOT
uv run --locked --extra dev python tools/phase2_5_lab.py fault --scenario F6 --confirm-generated-only --fault-duration 10 --state-root $env:HCAM_PHASE2_5_STATE_ROOT
```

F6 blocks only C04's private RTSP inference proxy. Its HLS/WHEP preview path
remains attached directly to MediaMTX, and the dashboard must not report RTSP
inference as healthy merely because preview is available.

## Evidence And Cleanup

Build evidence while the stack and media are present, then stop and verify the
retained metadata after the MP4 files are removed:

```powershell
uv run --locked --extra dev python tools/phase2_5_evidence.py build --require-runtime --state-root $env:HCAM_PHASE2_5_STATE_ROOT
uv run --locked --extra dev python tools/phase2_5_lab.py stop --state-root $env:HCAM_PHASE2_5_STATE_ROOT
uv run --locked --extra dev python tools/phase2_5_evidence.py check --state-root $env:HCAM_PHASE2_5_STATE_ROOT
```

`stop` removes containers, disposable volumes, and generated MP4 files. It
retains only lab catalogue state and sanitized evidence. `clean-media` can be
used when the stack is already stopped.

Normal container recreation preserves already validated generated fixtures.
The runner's `stop` command creates an explicit generated-only cleanup request
before Compose shutdown and independently removes the fixture directory, so an
image update cannot race a new publisher while final cleanup remains explicit.

## Troubleshooting

| Safe code | Meaning | Action |
| --- | --- | --- |
| `docker_engine_unavailable` | Docker CLI exists but engine is not running | Start Docker Desktop/Engine and rerun `doctor` |
| `insufficient_free_disk` | Selected local state disk has under 512 MiB | Choose another local SSD path |
| `fixture_encoder_failed` | Selected encoder failed a real fixture | Use `auto` or `cpu`; inspect host driver/FFmpeg separately |
| `fixture_probe_failed` | FFprobe cannot validate generated output | Verify FFmpeg installation and local file access |
| `fixture_h264_b_frames_present` | Encoder emitted H.264 B-frames that WHEP cannot relay | Select `auto` or `cpu`, regenerate, and do not bypass the probe |
| `docker_compose_failed` | Compose build/config/start failed | Run `config`, verify drive sharing, ports, and GPU overlay |
| `catalogue_capacity_assertion_failed` | Runtime is not 50 records/30 live | Stop, remove stale lab state if disposable, and start clean |
| `generated_lab_confirmation_required` | Fault command lacked explicit confirmation | Add `--confirm-generated-only` |

Never work around a failure by adding unapproved external hosts, disabling
certificate checks, storing tokens in URLs, enabling recording, or lowering the
declared validation tier. Online use is limited to the exact public catalogue
and returned transport locations enforced by the adapter policy.
