# P3.6 LAB-LAPTOP-01 Sanitized Inventory R0

Status: complete under `D-P3.6-INVENTORY-R0-AUTH` on 2026-08-29.

Machine-readable inventory:
[`p3-6-inventory-lab-laptop-01-r0.json`](../../contracts/phase-3/p3-6-inventory-lab-laptop-01-r0.json).

Authorization record:
[`p3-6-inventory-authorization.json`](../../contracts/phase-3/p3-6-inventory-authorization.json).

Inventory SHA-256:
`0E702718390FB6C373F0FC189CB58D0E79BB7FE3B3EA39B5E5AFE0DE4D47CA1F`.

## Authorization Boundary

The owner authorized sanitized read-only inventory of hardware, OS, display
driver, and already-installed runtimes on logical node `LAB-LAPTOP-01` only.
The collection used no network, installation, download, container, Kubernetes,
model, inference, performance, stress, thermal, media/data, deployment, or
remote Git action.

Hostname, username, serial numbers, asset tags, MAC/IP addresses, network
configuration, personal paths, and raw device identifiers were neither
requested nor recorded.

## Observed Platform

| Area | Sanitized observation |
| --- | --- |
| OS | Microsoft Windows 10 Pro, version `10.0.19045`, build `19045`, 64-bit |
| CPU | Intel Core i5-8365U, 4 physical cores, 8 logical processors, 64-bit |
| Memory | 8 GiB total, two 4 GiB modules reported at 2400 MHz |
| Graphics | Intel UHD Graphics 620, driver `31.0.101.2137`, driver date 2025-08-28 |
| Discrete NVIDIA | Not observed; `nvidia-smi` inventory unavailable |
| PowerShell | `7.6.5` |
| Default Python | `3.14.6` |
| uv | `0.12.3` |
| FFmpeg / ffprobe | `7.1.1` full build |
| Docker CLI | `29.7.2`, build `a7dcaa6`; engine was not contacted |

The display API reported 1 GiB adapter memory for Intel UHD 620. Because this
is integrated graphics, the value is recorded only as shared-memory metadata;
it is not treated as dedicated VRAM or acceleration/capacity evidence.

The default Python 3.14 distribution did not report installed metadata for
ONNX, ONNX Runtime, OpenVINO, PyTorch, TorchVision, TensorRT, NumPy, or OpenCV.
This statement is intentionally narrow: project-managed or external runtime
paths were not enumerated, imported, initialized, or executed.

## Storage Observation

| Fixed volume | Size | Free | Free percentage |
| --- | ---: | ---: | ---: |
| `C:` | 188.47 GiB | 3.27 GiB | 1.74% |
| `E:` | 99.95 GiB | 6.28 GiB | 6.28% |
| `F:` | 188.47 GiB | 4.09 GiB | 2.17% |

All observed fixed volumes have less than seven percent free space. Model,
runtime, container, build-cache, or benchmark work would risk exhaustion and
must not begin until a separately reviewed storage plan provides sufficient
bounded capacity. The inventory did not inspect or use `B:`.

## Profile Assessment

### `portable_cpu`

The factual hardware inventory is complete, but the profile is not yet
approved. The machine requires conservative memory, concurrency, batch, queue,
sampling, preview, and optional-enrichment settings. Exact runtime, generated
workload, numeric resource bounds, and owner approval remain pending.

### `local_accelerated`

Not established on this machine. Intel CPU/iGPU OpenVINO feasibility may be
researched later, but no provider support, decoder capacity, parity, speedup,
quality, or stability result exists. A stronger collaborator laptop remains a
separate profile and has not been inventoried.

### `capacity_target`

Not established. This inventory supports no C10, C50, server, cluster,
procurement, production, or statewide claim.

## Effect On Gates

- `P36-U1` is complete.
- `P36-G2` remains blocked: current-laptop inventory is only one input to the
  portable manifest, while exact runtime/workload bounds, the accelerated
  machine, and the capacity target remain unresolved.
- `P36-G1`, `P36-G4`, and `P36-G5` are unchanged and blocked.
- The earlier `D-P3.6-START` statement remains non-effective.

## Continuing Non-Authorization

This inventory authorizes no application, scheduler, runtime, model, download,
dependency, driver, dashboard, container, Kubernetes, inference, benchmark,
camera/media/data access, deployment, remote Git, P3.7, or later action.
