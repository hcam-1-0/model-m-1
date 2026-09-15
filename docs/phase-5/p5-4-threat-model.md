# P5.4 Security, Privacy, Human-Factors, And Overclaim Threat Model

Status: planning baseline; no runtime or operational validation claim

## Protected Properties

P5.4 must protect authorization scope, analytical meaning, evidence provenance,
uncertainty, review independence, chronology, correction visibility,
concurrency, field minimization, operator attention, accessibility, and the
boundary between review and external action.

## Threat Catalogue

| ID | Threat | Required control | Validation direction |
| --- | --- | --- | --- |
| T01 | Observation, inference, hypothesis, candidate, and alert are visually collapsed | Distinct nouns, icons, semantic banners, schemas, and actions | Snapshot and semantic-role assertions |
| T02 | Score is displayed as identity probability | Calibration class and limits; prohibit identity percentage copy | Forbidden-language and fixture tests |
| T03 | Hypothesis is presented as confirmed fact | Persistent falsifiable-hypothesis label and evidence roles | Content and accessibility-name checks |
| T04 | Candidate is presented as a database match | `identity_not_established`, field-level matrix, abstention | Candidate hostile fixtures |
| T05 | Proposed alert is presented as operational alert | Exact proposed lifecycle vocabulary and non-effect copy | Route/title/action assertions |
| T06 | Procedural priority is interpreted as criminal severity | Label priority as workflow ordering and expose source | Sort and copy tests |
| T07 | Contradicting or missing evidence is hidden below supporting evidence | Equal first-class evidence groups and summary counts | Generated contradiction cases |
| T08 | Stale, retracted, or superseded evidence remains action-enabled | Visible state, mutation disable, authoritative refetch | Correction/staleness state matrix |
| T09 | Graph layout implies importance, causality, or confidence | Layout disclaimer, neutral sizing, no centrality claim | Visual and content checks |
| T10 | Truncated graph appears complete | Node/edge/depth/window bounds and omitted counts always visible | Boundary and truncation vectors |
| T11 | Client expands hidden relationships or performs inference | Server-bounded projections only; new expansion request | Network/mock contract assertions |
| T12 | Spatial proximity is presented as association | Precision and proximity labels; table equivalence; no causal copy | Map/list parity tests |
| T13 | Sensitive location precision is overexposed | Server minimization, purpose scope, precision class | Forbidden-coordinate fixtures |
| T14 | Rule prose drifts from the executed revision | Exact rule revision and typed trace are authoritative | Mismatched-summary fixture |
| T15 | Failed or shadow rule looks approved | Lifecycle and evaluation-time state shown together | Rule-state matrix |
| T16 | Untrusted labels or reasons inject script or markup | Render as text, schema bounds, CSP, no raw HTML | XSS payload fixtures |
| T17 | Provider destination, credential, or raw response reaches browser | Field allowlist and recursive forbidden-key scan | Deep-object leakage tests |
| T18 | Cross-department object existence leaks through error or cache | Server scope, uniform denial, query partition and purge | Department transition tests |
| T19 | UI visibility is treated as authorization | Server capabilities for every read and mutation | Direct command-denial tests |
| T20 | Administrator role gains reviewer authority by implication | Explicit capability composition and separation of duties | Role matrix tests |
| T21 | Reviewer identity is confused across windows or session changes | Current session banner and per-window revalidation | Multi-window generated cases |
| T22 | One actor satisfies multiple independent quorum slots | Server-enforced actor uniqueness and attributable entries | Duplicate actor vectors |
| T23 | Author or conflicted actor reviews own work without policy | Server conflict-of-interest capability and denial reason | Policy-denial vectors |
| T24 | Quorum race accepts stale decision | Strong ETag, expected revision, transaction, authoritative refetch | Concurrent command simulator |
| T25 | Missing `If-Match` overwrites newer state | Mutation wrapper requires strong ETag | Missing/weak ETag cases |
| T26 | Idempotency key is reused with different payload | Request fingerprint mismatch fails closed | Replay/mismatch vectors |
| T27 | Client automatically resubmits a conflicted review | No mutation retry; semantic compare and reconfirm | Request-count and UI-state tests |
| T28 | Event payload is treated as current truth or authority | Event invalidates only; HTTP confirms | Event/HTTP divergence fixtures |
| T29 | Unknown event version silently mutates state | Quarantine event and use polling/manual refresh | Unknown-version cases |
| T30 | Event flood causes refresh storm or hides urgent corrections | Coalesced scoped invalidation with bounded backoff | Burst and correction-priority tests |
| T31 | Review result triggers notification, dispatch, enforcement, or provider update | No external-action adapter, route, control, or event side effect | Forbidden command and import scans |
| T32 | Draft reason leaks through browser persistence or telemetry | Memory-only draft, purge on scope/logout, no value logging | Storage and telemetry scans |
| T33 | Free-text reason leaks protected content | Bounded optional rationale, warning, minimization, server validation | Oversize and sensitive-key vectors |
| T34 | Queue design causes alert fatigue or speed bias | Work age and load visibility, neutral default order, no speed leaderboard | Human-factors review and browser checks |
| T35 | Confirmation design nudges acceptance over rejection or abstention | Symmetric actions, neutral copy, review summary, safe cancel | Interaction and visual review |
| T36 | Correction is absent from an already-open view | Impact invalidation, stale banner, disable mutation, refetch | Multi-view correction scenario |
| T37 | Dynamic profile removes safeguards or semantic fields | Profile changes rendering capacity only | Cross-profile contract equivalence |
| T38 | Graph is inaccessible to keyboard or screen-reader users | Authoritative table, focusable enhanced projection, synchronized selection | Keyboard, name/role/value, axe tests |
| T39 | Color or motion is the only state signal | Text/icon/pattern redundancy, reduced motion | Contrast, color-loss, motion tests |
| T40 | Status announcements steal focus or overwhelm the operator | Polite bounded coalesced status; assertive only for critical draft/authority loss | Live-region count and focus tests |

## Trust Boundaries

```text
Untrusted/generated event hint
  -> event parser and version quarantine
  -> scoped cache invalidation
  -> authoritative HTTP API
  -> schema and field-minimization boundary
  -> P5.1 query/session/capability policy
  -> typed P5.4 domain projection
  -> page and accessible table/graph/map views

Memory-only review draft
  -> confirmation and current-policy check
  -> mutation wrapper with ETag and idempotency
  -> authoritative server transaction
  -> sanitized receipt
  -> HTTP refetch
```

The browser is never trusted to calculate quorum, determine allowed lifecycle
transitions, resolve identity, infer relationships, apply corrections, or
authorize a review.

## Misuse Cases

### Rubber-Stamp Review

An operator repeatedly accepts proposed alerts without examining evidence.
Controls: evidence-first layout, contradiction and correction summary before
actions, neutral action placement, bounded confirmation, attributable review,
workload indicators, and future audit analysis. The UI must not impose an
arbitrary dwell timer as proof of meaningful review.

### Score Hunting

An operator sorts only by highest score and treats the first candidate as an
identity. Controls: no default score sort, calibration class and limits,
field-level evidence, contradiction-first filters, abstention, and explicit
identity-not-established copy.

### Graph Overreach

An operator interprets a dense cluster or short path as organized activity.
Controls: bounded projection, neutral layout, typed edge semantics, evidence
role and time, table alternative, truncation disclosure, and no client
centrality or causal language.

### Scope Probing

An operator edits route IDs or follows an old deep link to another department.
Controls: server authorization, uniform denial, no resource-existence detail,
partitioned cache keys, purge on scope change, and opaque handoffs.

### External Action By Workflow Shortcut

An operator expects an accepted review to dispatch or notify. Controls: no
external-action controls or adapters, explicit non-effect confirmation, and
separate future authority for every downstream action.

## Failure Taxonomy

The consumer accepts only low-cardinality safe reason families:

- `unauthorized` and `forbidden_scope`;
- `not_found_or_not_visible`;
- `stale_representation` and `policy_changed`;
- `idempotency_mismatch` and `duplicate_command`;
- `quorum_not_satisfied` and `reviewer_not_independent`;
- `invalid_transition` and `invalid_reason`;
- `producer_partial`, `producer_unavailable`, and `event_lag`;
- `schema_rejected`, `unsupported_version`, and `internal_failure`.

Raw exceptions, SQL, provider data, identifiers, labels, reasons, evidence,
request bodies, event payloads, credentials, and destinations are not logged or
used as metric labels.

## Validation Boundary

The future P5.4 generated-only package should include deterministic normal,
partial, denied, hostile, stale, contradictory, abstaining, corrected,
conflicting, duplicate, event-divergent, and cross-profile cases. It may prove
consumer behavior against generated fixtures. It cannot prove legal
compliance, human decision quality, model validity, bias absence, production
security, operational readiness, or fitness for policing.
