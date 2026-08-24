# Security, Privacy, And Safety

## Safety Position

Phase 3 outputs are probabilistic machine observations. They may assist a human
reviewer but cannot establish identity, intent, guilt, ownership, or grounds for
enforcement. No Phase 3 path may autonomously dispatch, detain, penalize, or
escalate a person or vehicle.

## Threat Model

| Threat | Example impact | Required control direction |
| --- | --- | --- |
| Malformed or hostile media | Decoder compromise or worker crash | Isolated bounded decoder, patched dependencies, fuzz/negative tests |
| Adversarial scene or object | Missed or false detection | Slice/robustness tests, confidence limits, human review |
| Poisoned dataset or labels | Backdoored or biased model | Provenance, access control, QA, manifests, immutable lineage |
| Malicious model artifact | Code execution or exfiltration | Approved formats, signatures, sandbox, egress deny, scanning |
| Artifact substitution | Undeclared model behavior | Digest verification and immutable deployment record |
| Forged/replayed events | False downstream intelligence | Authenticated channel, event IDs, producer identity, deduplication |
| Resource exhaustion | Queue growth and stale alerts | Admission control, limits, backpressure, circuit breaking |
| Cross-department leakage | Unauthorized observation access | Department scope, service identity, authorization tests |
| Sensitive output leakage | Tracking or plate exposure | Data minimization, field policy, encryption, retention, audit |
| Metrics/log cardinality leak | Camera/person detail in telemetry | Low-cardinality labels and structured redaction tests |
| Insider misuse | Unauthorized search/export/config | Least privilege, reason, approval, immutable audit, monitoring |

## Prohibited Technical Functions

- face embeddings, face recognition, biometric identification, or biometric
  watchlists;
- person re-identification or persistent appearance embeddings;
- sensitive-trait, emotion, intent, criminality, or individual risk inference;
- arbitrary model upload or runtime execution;
- direct camera credentials or unrestricted source-network access;
- default frame, crop, snapshot, or video persistence;
- silent reuse of analytics data for training;
- autonomous enforcement or alert escalation.

These are enforceable negative requirements with tests, not only documentation.

## Service And Network Boundaries

- Control-plane API, scheduler, decoder, inference, artifact registry, metadata
  store, and event delivery use separate least-privilege identities.
- Workers receive a short-lived internal media grant or approved local media
  mount, not a camera credential or reusable operator playback token.
- Decoder and inference workloads deny general egress and cannot resolve
  arbitrary source or artifact URLs.
- Artifact stores and event channels require authenticated encrypted transport.
- Production requires network policy outside application validation.
- Secrets use the Phase 2 provider boundary or an approved production secret
  manager; local file providers remain lab-only.

## Privacy By Design

- Process raw media in memory and as close to the source as practical.
- Emit the minimum geometry, class, confidence, and provenance needed by the
  approved capability.
- Keep anonymous track IDs short-lived and stream-scoped.
- Do not emit appearance descriptors or images as event evidence.
- Treat plate text as sensitive derived data with stricter access and retention
  than generic object counts.
- Separate operational aggregates from event-level records.
- Define retention and deletion by data class before enabling persistence.
- Make training reuse an explicit new purpose requiring approval.

## Human Review

Every analytic event begins as `unreviewed`. A future reviewer workflow must
display source camera, relevant authorized media, time, model/pipeline version,
confidence, rule reason, known limitations, and alternative OCR hypotheses.

Review actions are `confirmed`, `rejected`, `uncertain`, or `not_reviewable` and
record actor, reason, time, and policy version. Human confirmation does not
rewrite the model output; it creates a separate review record.

## Audit Requirements

Audit at minimum:

- analytics assignment create/change/pause/delete;
- model/dataset registration, approval, alias, promotion, rollback, retirement;
- zone, line, threshold, sampling, tracker, and retention-policy changes;
- event-level sensitive reads and plate-text searches;
- media review grants, exports, and denied access;
- worker artifact resolution and signature failure;
- emergency override, capability suspension, and incident response.

Audit payloads contain safe identifiers and hashes, never model bytes, media,
credentials, or unrestricted OCR text.

## Abuse And Misuse Review

Each capability card documents intended users, intended decisions, foreseeable
misuse, affected groups, false-positive and false-negative harms, operator
workload, contest/appeal path where applicable, and suspension owner. The review
uses NIST AI RMF's Govern, Map, Measure, and Manage functions as a risk-structure
reference; it is not a claim of certification.

## Security Validation

Before an analytics worker can leave the synthetic lab, tests cover:

- malformed, truncated, oversized, slow, and codec-changing media;
- malicious/invalid model files, signature mismatch, and registry outage;
- path traversal, symlink escape, arbitrary URL, redirect, and proxy bypass;
- credentials/media/plate text in logs, metrics, traces, exceptions, and events;
- authorization, department isolation, reason headers, and audit completeness;
- event replay, duplicates, out-of-order data, and oversized payloads;
- CPU/GPU/memory/process exhaustion and restart loops;
- rollback, kill switch, dependency outage, and recovery.

### P3.0 Control-Plane Evidence

The current bounded implementation covers only control-plane threats:

- strict schemas and recursive inspection reject media, locator, credential,
  biometric, Government, owner-record, and watchlist fields or URL/bearer/key
  values;
- role and department tests cover authorized reads/mutations, hidden cross-
  department resources, required reasons, and no-store responses;
- request, service, model, and database layers independently prevent activation;
- optimistic ETags, immutable revisions, audit records, and transactionally
  validated stream-partitioned outbox events cover configuration integrity; and
- synthetic tests prove assignment operations do not invoke the runtime adapter;
- sanitized 422 responses omit rejected values and validation contexts; and
- aggregate metrics/dashboard/alerts exclude assignment, stream, camera, actor,
  model, locator, and rejected-value labels.

This does not close decoder, model-artifact, runtime sandbox, media-path,
resource-exhaustion, kill-switch, or operational recovery threats because those
components do not exist yet. Their tests remain gates for P3.1 and later rather
than evidence implied by P3.0.

## Kill Switch And Incident Response

The owner or authorized security operator must be able to suspend one
assignment, capability, model version, department, processing node, or the
entire analytics plane without disabling camera registry and stream health.
Suspension is audited, idempotent, visible in health, and blocks automatic
restart until the applicable policy allows recovery.
