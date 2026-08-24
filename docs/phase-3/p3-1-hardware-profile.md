# P3.1 Developer Hardware Profile

Profile ID: `LAB-LAPTOP-01`

Captured: 2026-08-24

Purpose: generated-fixture correctness, manifest validation, metric goldens,
clean-machine reproducibility, and small CPU baselines. This profile is not a
production, GPU, C10/C50, or statewide-capacity target.

## Current Profile

| Component | Recorded value |
| --- | --- |
| CPU | Intel Core i5-8365U, 4 cores, 8 logical processors |
| Memory | 7.2 GiB reported physical memory |
| GPU | Intel UHD Graphics 620; 1 GiB adapter memory reported by Windows |
| Discrete accelerator | None observed in the captured Windows inventory |
| Operating system | Microsoft Windows 10 Pro, version 10.0.19045, build 19045 |
| Python | 3.14.6 |
| Docker engine | 28.5.2 |

## Authorized Uses

- schema and manifest validation;
- deterministic fixture generation;
- annotation/split/leakage validation;
- hand-computable metric golden tests;
- small generated-only CPU baselines; and
- source/wheel/container build verification.

## Prohibited Claims

Results from this laptop cannot establish production throughput, GPU parity,
C10/C50 capacity, long-duration stability, real-camera performance, or
statewide infrastructure sizing.

Every benchmark must record current CPU/GPU/OS/runtime details because driver,
OS, dependency, thermal, and background-load changes can invalidate comparison.
