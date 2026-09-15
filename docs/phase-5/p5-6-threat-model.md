# P5.6 Threat Model

Status date: 2026-09-10

Status: 72 planning threats documented; implementation and runtime remain closed

## Assets And Trust Boundaries

Protected assets include authorization decisions, organization and department
scope, identities and role bindings, administrative proposals and approvals,
policy/configuration revisions, secret references, provider metadata,
operational signals, security events, audit records, evidence references,
supply-chain evidence, recovery and capacity records, session state, and safe
failure information.

Primary trust boundaries are:

- browser to same-origin application/API edge;
- API edge to identity and policy producers;
- service authorization to PostgreSQL RLS;
- control-plane service to domain producer or future executor;
- operational/security/audit/evidence lane boundaries;
- application to observability, secret, provider, scanner, backup, cluster, and
  infrastructure adapters;
- department, organization, environment, and deployment-profile boundaries;
- generated fixture/evidence boundary versus any real system or data.

## Threat Register

| ID | Threat | Required control and validation |
| --- | --- | --- |
| T01 | Hidden route reveals a portal or record not present in navigation | Server authorizes every route/query; test direct deep links and denied state |
| T02 | Client changes role or capability state | Ignore client claims; server returns capability decisions and reasons |
| T03 | Cross-department identifier substitution | Bind subject, department, resource, and RLS; hostile-ID tests |
| T04 | Aggregate leaks rows from another department | Producer-scoped aggregates plus RLS parity and count-isolation tests |
| T05 | Pagination cursor crosses scope or filter revision | Signed/opaque scoped cursor; reject changed department, policy, or query |
| T06 | Background worker loses department scope | Typed scope envelope and non-owner RLS tests for worker paths |
| T07 | Database owner or bypass role silently defeats RLS | Dedicated non-owner application role, forced RLS where needed, assurance test |
| T08 | Wildcard or future resource permission expands access | Deny wildcards by policy or surface as high-risk finding; future-resource test |
| T09 | Role inheritance produces an unseen privilege | Exact direct/inherited capability table and server explanation |
| T10 | Stale policy or role revision authorizes a command | Bind policy revision and ETag; stale state forces refetch/reconsideration |
| T11 | Self-approval bypasses separation of duty | Server evaluates proposer/reviewer relationship and rejects ineligible actor |
| T12 | Administrator role becomes universal bypass | No role-name bypass; capability, scope, purpose, and state checks remain mandatory |
| T13 | UI enables action after session revocation | Revocation invalidation, authoritative refetch, immediate teardown, denial tests |
| T14 | Session or department switch leaves old data visible | Clear caches, drafts, routes, media/session state before loading new scope |
| T15 | CSRF or replay repeats a consequential request | Same-origin protection, CSRF control, idempotency key, nonce/receipt behavior |
| T16 | Authorization code, token, cookie, or assertion leaks in URL/log | Never place secrets in URL; redaction and navigation-history tests |
| T17 | Privileged action proceeds without required reauthentication | Server-produced step-up state; unavailable until trusted challenge completes |
| T18 | Break-glass becomes a permanent hidden superuser path | Default unavailable; future expiry, reason, strong auth, monitoring, and review |
| T19 | Generic JSON/YAML editor injects unsupported fields | Schema-specific forms, strict allowlists, canonical comparison, no raw editor |
| T20 | Mass assignment modifies immutable or out-of-scope fields | Server request schemas and field-level authorization; hostile extra-field tests |
| T21 | Stale ETag overwrites a concurrent change | Strong ETag/If-Match plus exact revision comparison and no last-write-wins |
| T22 | Automatic retry duplicates a command | Commands never auto-retry; idempotency receipt and explicit outcome recovery |
| T23 | Rollback erases history or reactivates unsafe state | Rollback is a new append-only proposal with current validation and approval |
| T24 | Scheduled change executes after approval or policy expires | Revalidate actor, policy, prerequisites, revision, and expiry at execution time |
| T25 | Blast-radius preview omits a dependency | Typed dependency closure, completeness/unknown markers, execution blocked on gaps |
| T26 | Client preview is mistaken for applied state | Persistent non-effective label and separate executor/effect receipt requirement |
| T27 | Kill switch is exposed as an immediate UI toggle | Revisioned proposal and authoritative effective projection; no direct toggle |
| T28 | Feature flag fail-open enables capability | Typed default-deny fallback and explicit provider unavailable state |
| T29 | Flag targeting uses sensitive or spoofable client context | Server evaluation with minimized context; client values untrusted |
| T30 | Configuration dependency cycle causes inconsistent activation | Cycle detection, topological validation, blocked effect, generated cycle tests |
| T31 | Secret value is returned through API or browser state | Opaque `secret_ref` only; schemas reject value-like fields |
| T32 | Secret leaks through errors, telemetry, audit, clipboard, or URL | Central redaction, safe reasons, no reveal/copy, hostile secret-shape tests |
| T33 | Listing secret refs reveals excess inventory | Capability-scoped metadata, bounded pagination, minimized labels, access review |
| T34 | Provider connection test becomes SSRF or credential oracle | No browser/provider test in P5.6; future exact destination policy and safe result |
| T35 | Certificate or rotation status is presented as verified security | Display source, observed time, method, freshness, and limitations separately |
| T36 | Revoked provider remains apparently active | Revisioned revocation state, freshness, kill-switch relation, refetch on event |
| T37 | Operational log is treated as immutable audit | Separate schemas, storage authority, labels, navigation, and integrity semantics |
| T38 | Security event is presented as proof of attack or guilt | Qualified event language, source/limitations, no identity/criminality conclusion |
| T39 | Evidence integrity is presented as factual truth | Preserve P5.5 orthogonal evidence states and explicit non-truth language |
| T40 | Combined search silently drops or merges lane records | Derived search is disabled/non-authoritative; source-specific confirmation |
| T41 | Raw request/response or exception exposes sensitive data | Typed fields, bounded payloads, sanitization, no raw body/stack output |
| T42 | High-cardinality labels leak IDs or exhaust telemetry backend | Allowlisted low-cardinality labels; IDs only as protected record attributes |
| T43 | Missing telemetry is displayed as healthy | Unknown/stale/partial states and coverage/completeness fields |
| T44 | Trace baggage carries credentials or personal data | Attribute allowlist and propagation policy; no arbitrary baggage display |
| T45 | Audit actor or event can be edited or deleted in UI | Read-only immutable references; append-only correction/annotation producer only |
| T46 | Clock skew reorders administrative or security chronology | Record sequence authority plus qualified event/observed time and clock state |
| T47 | Security dashboard becomes a surveillance view of staff | Minimized aggregates, bounded purposes, role controls, no behavioral conclusions |
| T48 | Audit export or bulk query exfiltrates records | Export absent; bounded pages/windows; purpose and capability enforcement |
| T49 | `no vulnerabilities` is inferred from stale or missing scan | Show source, age, coverage, applicability, exception, and not-run states |
| T50 | SBOM omits transitive/service dependencies but appears complete | Composition/completeness fields and dependency coverage limitations |
| T51 | Provenance assertion is displayed as verified provenance | Separate assertion, verification, trust root, subject, and policy outcome |
| T52 | License metadata becomes a legal clearance claim | Distinguish detected assertion, review status, exception, and legal unknown |
| T53 | Dependency detail enables unsafe external link or download | Opaque refs and exact safe links only; no artifact acquisition |
| T54 | Accepted build is confused with deployed runtime | Separate source/build/release/deployment/runtime identities and observations |
| T55 | Service heartbeat masks dependency or data-quality failure | Multidimensional health, dependency state, data quality, and limitations |
| T56 | SLO target is invented from generated capacity evidence | Targets remain unset or policy-referenced; no production extrapolation |
| T57 | Error-budget chart hides missing samples | Coverage, window, source, missing intervals, and completeness table |
| T58 | Queue control retries or requeues real work unintentionally | All controls unavailable in P5.6; future typed command and idempotency |
| T59 | Dead-letter payload browsing exposes private or prohibited data | Metadata-only aggregate and opaque job refs; no payload display |
| T60 | Recovery of abandoned work duplicates side effects | Future lease, ownership, idempotency, attempt, and terminal-state checks |
| T61 | Circuit or degradation control creates cascading outage | Dependency impact, bounded policy, expiry, rollback, and independent approval |
| T62 | Health refresh creates polling storm | Resource-profile cadence, visibility pause, jitter, backoff, and shared queries |
| T63 | Backup success is shown without restore evidence | Separate backup observation and restore/drill result with age and limitations |
| T64 | Recovery plan button triggers destructive or irreversible action | Non-operative preview only; no executor or direct infrastructure connection |
| T65 | RPO/RTO values become unapproved commitments | Policy refs and unset state; owner/governance decision outside P5.6 |
| T66 | Maintenance window hides active degradation or security issue | Preserve overlapping states, dependencies, and blocked/conflict outcome |
| T67 | Resource profile changes authority, data scope, or truth | Cross-profile equivalence tests; only density/cadence/visual detail changes |
| T68 | Client spoofs GPU/server/Kubernetes capability | Server-bounded profile and generated capability source; no authority impact |
| T69 | Kubernetes projection implies cluster is connected or secure | Persistent desired/generated/not-validated labels; no cluster API |
| T70 | Accessibility alternative omits state or action constraints | Table/list parity tests for every visualization and workflow state |
| T71 | Localization changes identifiers, policy meaning, or reason codes | Localize descriptions only; stable machine identifiers and canonical values |
| T72 | Production, compliance, security, scale, or certification overclaim | Claims/limitations registry and acceptance checks block unsupported wording |

## Threat Coverage Groups

| Group | IDs | Count |
| --- | --- | ---: |
| Authorization and isolation | T01-T12 | 12 |
| Session, change, and concurrency | T13-T24 | 12 |
| Configuration, features, providers, and secrets | T25-T36 | 12 |
| Signals, audit, privacy, and chronology | T37-T48 | 12 |
| Supply chain, operations, and reliability | T49-T60 | 12 |
| Recovery, profiles, accessibility, and claims | T61-T72 | 12 |
| Total | T01-T72 | 72 |

## Abuse Cases To Preserve In Validation

- direct URL access to every unavailable route;
- cross-department list, detail, cursor, aggregate, event, and saved-view reuse;
- forged role, department, capability, policy revision, ETag, and resource
  profile;
- self-approval, stale approval, replayed command, duplicate idempotency key,
  and concurrent change;
- secret/token/cookie/credential-shaped strings in every user-visible and
  telemetry-capable field;
- markup, bidirectional text, control characters, oversized values, unknown
  enum values, and hostile external links;
- partial, stale, missing, contradictory, and not-configured producer states;
- high-frequency events, event gaps, out-of-order notifications, and reconnect;
- low-resource, enhanced, control-room, GPU-lab, server, and Kubernetes
  profile equivalence;
- keyboard-only, zoom, reflow, focus, screen-reader naming, reduced motion, and
  non-color state equivalence.

## Residual Risk

Generated-only validation cannot prove production identity, policy, database,
telemetry, backup, cluster, infrastructure, secret, provider, or audit behavior.
Those risks remain blocked producer gaps and require separately authorized
backend, integration, adversarial, environment, recovery, and deployment
validation before any operational claim or action.
