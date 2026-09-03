# P3.6 Portable Compatibility And Generated C1 Validation Proposal R0

Status: non-executable planning proposal complete; four U3C owner selections
are pending. No artifact, dependency, runtime, inference, hardware, profile,
implementation, deployment, or remote Git authority is granted.

## Purpose

The accepted U3B policy requires strict seven-input admission, a complete
immutable compatibility bundle, and deterministic generated-only `CONTRACT`
plus C1 `INFER` evidence. This proposal defines the next exact planning choices
without pretending that artifacts, runtime compatibility, or performance
evidence already exist.

Machine-readable records:

- [primary-source ledger](../../contracts/phase-3/p3-6-portable-compatibility-validation-research-sources.json);
- [technical proposal](../../contracts/phase-3/p3-6-portable-compatibility-validation-proposal.json);
- [owner decision packet](../../contracts/phase-3/p3-6-portable-compatibility-validation-decision-packet.json); and
- the immutable package manifest added after final hash verification.

## Research Basis

Official ONNX Runtime documentation establishes that:

- CPU sessions expose explicit intra-op and inter-op thread counts, sequential
  execution, spinning, and affinity controls; spinning trades additional CPU
  and power for responsiveness ([thread management](https://onnxruntime.ai/docs/performance/tune-performance/threading.html));
- basic graph optimizations are semantics-preserving and provider-independent,
  while higher or offline optimizations can become provider/hardware-sensitive
  ([graph optimizations](https://onnxruntime.ai/docs/performance/model-optimizations/graph-optimizations.html));
- memory arena, memory pattern, profiling, provider ordering, and other session
  behavior are explicit API choices ([Python API](https://onnxruntime.ai/docs/api/python/api_summary.html)); and
- profiling is opt-in and emits an artifact, so it remains disabled in the
  zero-retention baseline ([profiling example](https://onnxruntime.ai/docs/api/python/auto_examples/plot_profiling.html)).

These sources support configuration choices. They do not prove that any choice
meets H-CAM quality, latency, throughput, resource, recovery, or deployment
requirements on this or another machine.

## Compatibility Skeleton

The proposal targets `hcam-portable-cpu` using the historical YOLOX-Tiny
`DET-R0` reference, ONNX Runtime `1.29.0` candidate metadata from the existing
lock, `CPUExecutionProvider`, FP32, and ONNX.

This is not yet a valid shared compatibility manifest. It intentionally marks
the following unavailable:

- acquired and revalidated model/runtime artifacts;
- OCI references, provenance, SBOM, signatures, and vulnerability evidence;
- exact pipeline input/output/preprocess/postprocess digests;
- license and security review with expiry;
- validated fallback and rollback manifests; and
- promotion or resolver eligibility.

## Pending Owner Decisions

### D-P3.6-U3C-001: Runtime Session Configuration

**A. Deterministic low-contention CPU reference (recommended).** Use only
`CPUExecutionProvider`, FP32, sequential execution, one intra-op and one
inter-op thread, disabled spinning, OS-managed affinity, basic graph
optimization, CPU arena and memory pattern enabled, profiling disabled, no
optimized-model output, one session, batch one, one in-flight request, and a
two-item queue. Unexpected provider or precision means reject and safe-pause.

**B. ONNX Runtime performance defaults.** Use physical-core threading,
spinning, and all graph optimizations. This may improve speed but consumes more
CPU/power and is less stable as a shared laptop reference.

**C. Hardware-adaptive automatic tuning.** This matches the future platform
direction but requires implementation and measured policy evidence first.

**D. Defer.** Leaves the calibration environment non-reproducible.

### D-P3.6-U3C-002: Generated C1 Workload

**A. Bounded three-seed matrix (recommended).** Use 64 non-runtime contract
cases; zero, ramp, and seeded-uniform FP32 tensors; seeds `36001`-`36003`; three
cold starts; five warmups per seed; three repetitions of 30 measured inferences
per seed; an eight-submission burst admitting at most three; three dependency
failures; three safe shutdowns; ten-second per-inference, five-minute
per-scenario, and fifteen-minute total bounds; no background load; and zero raw
tensor/output retention.

**B. Minimal smoke.** Faster, but insufficient for queue, recovery, variance,
and objective-mode evidence.

**C. Resource-aggressive matrix.** Statistically larger but requires explicit
stress/thermal authority and is not appropriate for the first portable run.

**D. Defer.** Keeps workload values unresolved.

### D-P3.6-U3C-003: Acceptance Strategy

**A. Hard safety gates, calibration, then held-out validation (recommended).**
Predeclare no fallback, exact provider/precision, schema/finite/deterministic
output, zero retention/network, memory, queue, dependency-failure, shutdown,
and total-time ceilings. A later separately authorized stage performs
non-promotional generated calibration. Its results cannot promote anything.
Another sealed package must then declare performance thresholds and held-out
seeds before final validation.

This prevents the first run from being both tuning data and final evidence. It
also avoids inventing latency and throughput claims without measurement.

**B. Single-pass fixed thresholds.** Faster, but the numbers are weakly
justified and the same run becomes tuning and final evidence.

**C. Throughput-first.** Conflicts with balanced-default and fail-closed policy.

**D. Structural only.** Valid for `CONTRACT`, insufficient for profile
admission or capacity claims.

### D-P3.6-U3C-004: Bundle Lifecycle

**A. Five immutable revisions (recommended).** Use:

1. `R0`: unavailable planning skeleton;
2. `R1`: acquired, scanned, and supply-chain-reviewed artifacts;
3. `R2`: non-promotional generated calibration;
4. `R3`: held-out validation candidate; and
5. `R4`: eligible or rejected only after every resolver input and hard gate
   passes.

Each transition requires its own exact authority and immutable evidence.

**B. One mutable bundle.** Simpler but loses review and rollback boundaries.

**C. Candidate and approved only.** Conflates acquisition, calibration,
validation, and promotion.

**D. Runtime-generated state.** Dynamic but non-reproducible and unsuitable for
pre-admission review.

Recommended selection: `A/A/A/A`.

## Hard Safety Gates Proposed By Option A

The hard gates are planning values, not measured claims:

- exact CPU provider and FP32, with zero fallback;
- 100% schema-valid and finite outputs;
- 100% repeat digest match for the same bundle/input on the same node;
- 100% rejection of excess bounded-burst work;
- zero raw tensor/output retention and zero network attempts;
- at least `1024 MiB` available memory before starting;
- at most `2048 MiB` process RSS;
- at most `2000 ms` queue age and dependency-failure detection;
- at most `10000 ms` safe shutdown; and
- at most `900 seconds` total validation time.

Failure means reject or safe-pause. It never triggers automatic fallback,
threshold relaxation, profile activation, or promotion.

## Current Gate Effect

This proposal does not create a compatibility manifest, install ONNX Runtime,
acquire or verify artifacts, run a model, create validation evidence, or make
`portable_cpu` resolver-eligible. `P36-G2` remains blocked.

The four U3C choices are independent and remain unselected. Acceptance may not
be inferred from `continue`, earlier U3B acceptance, or another decision.

All inventory, acquisition, runtime, model, hardware, profile, container,
Kubernetes, camera/media/data, implementation, deployment, and remote Git
actions remain separately gated.
