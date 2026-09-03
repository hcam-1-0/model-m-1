# Product Scope

## Mission

Phase 3 converts authorized video into structured machine observations that
later H-CAM modules can search, correlate, review, and use to propose alerts.
It creates an analytics foundation, not an automated policing decision system.

## Primary Users

| User | Phase 3 need |
| --- | --- |
| Computer-vision engineer | Reproducible datasets, models, evaluations, and error analysis |
| Platform engineer | Stable contracts, scheduling, backpressure, and deployment controls |
| Security/data reviewer | Provenance, access, retention, audit, and risk evidence |
| Control-room evaluator | Reviewable output with source, time, confidence, and limitations |
| Project owner | Clear promotion gates and evidence for accepting each capability |

These roles describe expertise, not mandatory separation of approvers. The
accountable owner may approve model, dataset, operational-geometry, and
deployment records after the required evidence passes.

Operator-facing dashboards and operational alert workflows are later phases.
Phase 3 may expose test and administrative APIs only where needed to validate
the analytics subsystem.

## Required Baseline Capabilities

- person and vehicle detection on synthetic or authorized test media;
- selected neutral object classes needed by approved scenarios;
- anonymous multi-object tracking within a single camera stream;
- line crossing, zone entry/exit, occupancy, and dwell-time primitives;
- plate-region detection and OCR on synthetic or separately authorized plate
  data;
- versioned model and pipeline assignments;
- normalized observation, track, and analytic-event contracts;
- confidence, timing, quality, model, runtime, and processing-node provenance;
- replayable offline evaluation and bounded multi-stream benchmarks;
- operational metrics, audit events, failure reasons, and safe degradation.

## Capability Tiers

Phase 3 uses staged capability gates instead of treating every computer-vision
idea as equally mature.

- **Tier A, foundation:** detection, per-camera tracking, line/zone primitives,
  synthetic ANPR, contracts, metrics, and governance.
- **Tier B, scenario analytics:** crowd density, loitering, intrusion, and
  wrong-way movement after dataset and policy approval.
- **Tier C, high-consequence analytics:** abandoned-object, accident,
  fire/smoke, and weapon-like-object hypotheses only after dedicated risk,
  data, false-positive, and human-response review.

The tiers are delivery order and governance levels, not claims of accuracy.

## Explicit Non-Goals

- face detection for identity workflows, face recognition, or biometric
  templates;
- persistent person embeddings or person re-identification;
- cross-camera tracking or identity resolution;
- watchlists, wanted-person matching, or Government database queries;
- vehicle-owner lookup or automatic plate enforcement;
- emotion, ethnicity, religion, caste, health, gender, or other sensitive
  attribute inference;
- predictive policing, criminality scoring, or individual risk scores;
- autonomous dispatch, detention, enforcement, or evidence conclusions;
- uncontrolled recording, frame capture, or raw-video retention;
- training on Sentinel, police, or private CCTV without explicit authorization;
- claiming model, legal, ONVIF, security, or production conformance without the
  applicable formal evidence.

## Phase Boundary

```text
Phase 2                                  Phase 3
camera + stream + health                anonymous observation + local track
capability inventory                    line/zone analytic event
controlled playback                     model/pipeline provenance
        |                                      |
        +------------ trusted stream ----------+
                                               |
                                               v
Phase 4
correlation + authorized watchlists + alert policy + investigations
```

Phase 3 emits an `analytic_event`, not an operational `alert`. Phase 4 decides
whether multiple events and authorized external facts justify a proposed alert
and owns escalation and investigation workflows.

## Success Definition

Phase 3 is successful only when the required Tier A capabilities are
implemented through the approved contracts, validated against frozen datasets,
benchmarked on declared hardware, shown to fail safely, and accepted by the
owner. A visual demo alone is not acceptance evidence.

## Planning Assumptions To Verify

- The initial development environment is Windows with Docker Desktop, while
  GPU production candidates may require Linux deployment nodes.
- The existing Phase 2 MediaMTX gateway remains the controlled video boundary.
- The portable reference path can use ONNX artifacts when export fidelity is
  proven; native runtime artifacts remain possible behind adapters.
- Exact model families, licenses, target hardware, frame rates, latency SLOs,
  and dataset sources remain owner decisions backed by benchmarks.
