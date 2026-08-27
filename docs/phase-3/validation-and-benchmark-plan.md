# Validation And Benchmark Plan

## Evidence Principle

Validation must test the complete declared combination of dataset, model,
preprocessing, postprocessing, taxonomy, tracker, rules, runtime, precision,
hardware, and configuration. A model score copied from a paper or vendor page
is not H-CAM evidence.

The [P3.6 plan](p3-6-plan.md) makes runtime evidence explicitly layered as
`CONTRACT`, `INFER`, and `PIPE`, with model-family selection preceding runtime
selection. Its numeric gates and execution remain owner- and manifest-gated.

## Test Layers

| Layer | Purpose | Network/media rule |
| --- | --- | --- |
| Contract | Schema, bounds, compatibility, redaction, idempotency | Generated metadata only |
| Component | Pre/postprocessing, geometry, tracking, rules, adapters | Generated frames/sequences |
| Offline accuracy | Frozen labeled datasets and slices | Approved local dataset store |
| Pipeline integration | Decode through outbox and metadata persistence | Synthetic or authorized clips |
| Runtime parity | Compare reference and accelerated outputs | Same frozen inputs |
| Performance | Latency, throughput, resource use, overload | Declared 1/10/50 synthetic streams |
| Resilience/security | Fault injection and hostile inputs | Controlled isolated lab |
| Human factors | Review quality and workload | Synthetic/approved scenarios only |

CI remains fully deterministic and does not contact CCTV systems, download
models at test time, or require a GPU. Larger artifacts are pinned and supplied
through an approved cache or artifact store.

## Portfolio Comparison Design

The selected planning portfolio is evaluated in two funnels:

1. `DET-R0`, `DET-E1`, `DET-B1`, and `DET-A1` are compared as model families
   using frozen taxonomy, preprocessing intent, inputs, metric versions, and
   postprocessing semantics.
2. Only promoted model families enter runtime/provider comparison. Runtime
   optimization cannot be confused with model-quality selection.

`DET-R0` is the behavioral reference, not an assumed accuracy winner.
`DET-E1` represents constrained compute, `DET-B1` the balanced candidate, and
`DET-A1` the accuracy candidate. Candidate-specific input resolution is
preserved and declared; a second resolution-normalized diagnostic may be added
but cannot replace intended-deployment results.

OCR reports remain separate for `OCR-L0/L1`, `OCR-D0`, and `OCR-G0/G1`.
Unsupported-script routing, abstention, and script misrouting are measured.
No aggregate multilingual score can hide failure for Gujarati, Devanagari, or
Latin text.

## Accuracy Metrics

### Detection

- mAP across IoU 0.50:0.95 and AP50;
- precision, recall, F1, and average precision per H-CAM class;
- metrics by object size, occlusion, truncation, lighting, camera angle, scene,
  weather/synthetic condition, and resolution;
- confusion matrix, duplicate detections, and missed-object counts;
- confidence calibration such as expected calibration error or Brier score when
  downstream thresholds rely on confidence.

### Per-Camera Tracking

- HOTA and IDF1 as primary complementary metrics;
- MOTA, identity switches, fragmentations, mostly-tracked/lost tracks;
- track start delay, end delay, and recovery after occlusion;
- separate reports by density, object size, camera motion, and discontinuity;
- restart and tracker-epoch correctness.

Tracking metrics do not justify cross-camera identity use.

### ANPR

- plate-region precision/recall and IoU;
- exact normalized-plate match rate;
- character accuracy/edit distance and top-k alternative coverage;
- results by plate format, character length, perspective, blur, illumination,
  occlusion, and synthetic generator family;
- separate detection, OCR, and normalization errors.

ANPR evaluation is synthetic or explicitly authorized. No owner lookup or
enforcement metric belongs in Phase 3.

### Rules And Scenario Events

- event precision, recall, false events per stream-hour, and missed events;
- onset/termination timing error and decode-to-event latency;
- boundary jitter and duplicate-event rate;
- deterministic replay: identical ordered inputs produce identical rule events;
- reviewer agreement and review time for riskier scenario hypotheses.

## Performance Metrics

- source frames received, sampled, decoded, inferred, skipped, and dropped;
- decode, preprocess, queue, infer, postprocess, track, rule, publish, and total
  decode-to-event p50/p95/p99 latency;
- per-stream effective frames per second and maximum queue age;
- CPU, RAM, GPU utilization/memory, decoder sessions, network, and power where
  measurable;
- model load/warmup time, restart time, and assignment recovery time;
- event volume and payload bytes per stream-hour;
- quality and latency under C1, C10, and C50 workloads.

Metric labels remain low cardinality. Camera IDs, stream IDs, plate strings,
users, file paths, model URLs, and dataset paths are not metric labels.

## Benchmark Manifest

Every result is accompanied by:

- run ID, UTC time, operator, source commit, and uncommitted-change state;
- dataset/fixture manifests and hashes;
- model, pipeline, taxonomy, tracker, rules, runtime, and container digests;
- full hardware/driver/OS profile;
- stream count, codec, resolution, source frame rate, sampling target, and
  duration;
- warmup, repetitions, batch/concurrency settings, and random seeds;
- raw machine-readable results, summary, failures, and comparison baseline.

The harness must produce a nonzero exit for invalid evidence or unmet approved
gates. Individual scenario failures remain visible rather than being averaged
away.

Promotion is conjunctive: artifact/legal, export parity, contract, slice
quality, resource, downstream, runtime, and accountable-owner approval gates
must all pass. Separate-person review is optional. A weighted score may aid
comparison only after every hard gate passes.
Each rejection records the failed gate so a larger model is not run merely to
complete a benchmark table.

## Slice Matrix

The minimum slice plan considers:

- day/night, bright/dim, glare/backlight, rain/fog simulation;
- low/high resolution and compression artifacts;
- near/far, small/large, partial/fully visible objects;
- sparse/crowded scenes and static/moving backgrounds;
- fixed and intentionally simulated camera shake;
- vehicle class, plate layout, orientation, and script/font where approved;
- decoder discontinuity, repeated frames, timestamp jump, and reconnect.

Slices are chosen from intended use and risk analysis. Aggregate performance
cannot hide a failing safety-relevant slice.

## Resilience And Degradation Scenarios

- stream unavailable, stalls, reconnects, changes codec, or jumps timestamps;
- model fails to load, times out, returns malformed tensors, or exhausts memory;
- artifact registry, metadata database, or event sink is unavailable;
- worker is killed during processing or outbox publication;
- queue reaches limits and sampling is reduced;
- configuration changes during an active tracker epoch;
- duplicate, late, reordered, or replayed events arrive;
- system clock differs from source media time;
- rollback and kill switch operate during load.

Expected state, safe reason code, retry policy, data-loss statement, audit event,
and recovery evidence are specified for every scenario before testing.

## Initial Engineering Gates

These gates can be fixed before model selection:

- 100% pass for contract fixtures, bounds, compatibility, and negative PII/
  credential tests;
- no raw media, crop, embedding, secret, source URL, or unrestricted plate text
  in events, logs, traces, metrics, or Git fixtures;
- deterministic rule results for deterministic ordered inputs;
- no unbounded queue, memory growth, retry loop, or crash propagation;
- branch coverage of at least 90% for new deterministic Phase 3 application
  logic, with risk-based integration tests beyond coverage;
- migration upgrade/downgrade and concurrent PostgreSQL worker evidence;
- clean dependency/model license and vulnerability review under the declared
  policy;
- successful rollback and kill-switch drills.

Accuracy, latency, throughput, and per-stream sampling targets cannot honestly
be fixed until a use-case dataset and target hardware profile are approved.
Phase 3 milestone P3.1 must propose numeric targets from a measured baseline;
the owner must approve them before model promotion.

## Acceptance Evidence

Final Phase 3 acceptance requires:

1. approved requirements, contracts, datasets, model cards, risk reviews, and
   numeric gates;
2. reproducible CI and frozen offline accuracy reports;
3. runtime parity and declared-hardware benchmark reports;
4. C1/C10/C50 performance and degradation evidence, or an explicitly approved
   narrower scale statement;
5. security, privacy, authorization, audit, rollback, and recovery evidence;
6. controlled end-to-end synthetic demonstration with no real CCTV dependency;
7. explicit owner acceptance.

No single accuracy score, screenshot, demo, or green unit-test suite substitutes
for this evidence set.
