# P4.4 Owner Decisions And Reconciliation

Status date: 2026-09-05

Status: all ten P4.4 design decisions are recorded and effective for planning
reconciliation only. They do not authorize implementation, runtime execution,
credentials, provider or workflow-engine connections, network access, real
data, cameras/media, operational actions, deployment, or remote Git.

Owner: `mayank-admin`

Planning predecessor: `P4.4-PLANNING-R0`, SHA-256
`16CA0D6723AF2ACF32E68D834A7EFE2C557A408DD71EF82A9B2120CCE015C01E`.

## Recorded Selection

```text
D-P4.4-001: C
D-P4.4-002: D
D-P4.4-003: A, with capability for C and D
D-P4.4-004: A
D-P4.4-005: A
D-P4.4-006: A, with a request to support D
D-P4.4-007: A
D-P4.4-008: C
D-P4.4-009: A
D-P4.4-010: A
```

The phrases "capable of" and "try to do" are binding architecture capability
requests, not permission to activate the riskier option as written. The
reconciled design provides typed extension surfaces and generated fakes while
keeping the selected A control authoritative. A future real secret backend,
authentication extension, or workflow engine still requires an exact separate
authorization.

## Reconciled Profile

| Decision | Planning binding |
| --- | --- |
| `D-P4.4-001:C` | Shared typed integration kernel, immutable provider manifests, and provider-specific static adapters |
| `D-P4.4-002:D` | In-process generated provider first; loopback HTTP/TLS simulator only under a later exact authorization |
| `D-P4.4-003:A+[C,D capability]` | Closed typed auth and per-attempt leases remain canonical; encrypted database envelopes and constrained extension profiles are optional disabled backends |
| `D-P4.4-004:A` | Exact compiled destination route, verified service identity, application checks, and deployment-level egress controls |
| `D-P4.4-005:A` | Dedicated normalized catalogue snapshots plus minimized result cache and explicit freshness |
| `D-P4.4-006:A+[D capability]` | Durable PostgreSQL job truth plus a generated executor simulator and future typed external workflow adapter |
| `D-P4.4-007:A` | Deterministic field-specific evidence, contradiction, bounded ranking, and abstention |
| `D-P4.4-008:C` | Manual query and generated hypothesis-enrichment lanes, independently switchable and default-off |
| `D-P4.4-009:A` | Versioned provider lifecycle plus hierarchical durable revocation and kill switches |
| `D-P4.4-010:A` | Zero durable raw provider response, minimized evidence, and separately sanitized telemetry |

## D-P4.4-001: Typed Kernel And Static Adapters

Option C is selected as written. The integration kernel owns provider-neutral
contracts for purpose, fields, request identity, jobs, transport policy,
normalization, evidence, candidates, review, revocation, and telemetry.

Each provider-specific adapter is static, versioned, allowlisted, and compiled
against an immutable provider manifest. An adapter may map typed fields and
operations but cannot introduce a destination, method, path, header, secret,
parser, authority class, or retention rule that the compiled manifest does not
permit. A runtime URL or generic configuration file is not provider authority.

## D-P4.4-002: Staged Generated Transport Validation

Option D combines the safe parts of A and B as ordered gates:

1. Tier A uses only an in-process generated provider with invented,
   non-issuable records and no socket.
2. Contract, parser, policy, timeout, truncation, redaction, revocation, and
   candidate behavior are proven at the in-process boundary.
3. A separate future authorization may enable a loopback-only HTTP/TLS
   simulator bound to an exact local address, port, certificate, and route.
4. Loopback success cannot authorize a real provider or support a conformance,
   interoperability, scale, latency, or deployment claim.

The current decision records the architecture. It does not authorize the
loopback process, socket, certificate generation, or network attempt.

## D-P4.4-003: Typed Authentication With Guarded C And D Capability

Option A is authoritative. Every operation selects one closed authentication
profile, bound to provider version, operation, purpose, audience, destination,
and field policy. Credentials are resolved from an opaque `secret_ref` for one
attempt, exposed through a bounded lease, and discarded before logging,
metrics, audit, exceptions, retries, or persistence.

### C capability: encrypted database envelope provider

The architecture may include a disabled `DatabaseEnvelopeSecretProvider` that
stores only authenticated encrypted envelopes and non-secret metadata. The
normal provider configuration still stores only an opaque reference.

This backend requires all of the following before implementation or use:

- an external or independently controlled key-encryption key;
- envelope encryption with algorithm and key-version allowlists;
- separation between database administration and key administration;
- authenticated context binding to department, provider version, auth profile,
  purpose, and secret generation;
- rotation, revocation, lease expiry, backup/restore, deletion, and audit
  behavior proven with generated secret canaries;
- no plaintext, reversible debug output, raw exception, credential URL,
  environment fallback, or database query surface;
- separate exact authorization for backend implementation and another for any
  real secret migration or use.

The database is not silently promoted into the default credential vault. The
generated tier keeps this backend disabled and uses only `none_generated` plus
the fail-closed unconfigured provider.

### D capability: constrained authentication extensions

The architecture may support additional provider authentication through a
typed `AuthProfileExtension` contract. It does not accept the unsafe
"unconstrained plugin" semantics literally.

An extension must be signed or digest-bound, explicitly allowlisted, versioned,
schema checked, and registered before startup. It may emit only fields declared
by a closed profile schema. The kernel still controls destinations, headers,
canonicalization, redaction, retries, telemetry, lease disposal, and kill
switches. Dynamic code downloads, arbitrary header mutation, runtime imports,
secret-provider bypass, redirect/proxy changes, and direct socket creation are
denied.

This gives future provider flexibility while retaining one auditable security
boundary. No extension implementation, loading, or authentication attempt is
authorized now.

## D-P4.4-004: Exact Destination And Trust Policy

Option A is selected as written. A compiled operation binds exact scheme,
service identity, port, approved address policy, path-template ID, method,
query/header slots, trust profile, response media type, response size, timeout,
and retry class.

Redirects and environment proxies remain disabled. Future real HTTPS requires
verified service identity and an approved trust bundle. DNS answers and every
provider-returned URL are revalidated. Production also requires network egress
policy; application validation alone is not a deployment control.

## D-P4.4-005: Dedicated Catalogue And Freshness State

Option A is selected as written. Provider catalogue observations are normalized
into versioned, department-scoped snapshots with stable fingerprints,
first/last observation times, explicit freshness, source-provider version, and
field-minimization policy.

Unchanged observations deduplicate. Changed stable capabilities create history.
Raw provider responses are not retained. Stale, missing, revoked, partial, and
contradictory observations remain visible states rather than being silently
treated as current truth.

## D-P4.4-006: Durable Jobs With Future Workflow Adapter

Option A is authoritative. PostgreSQL owns semantic query identity, job state,
attempts, leases, retry classification, deadlines, cancellation, concurrency
and cost budgets, circuit state, revocation, quarantine, and terminal outcome.
The internal worker remains bounded and recoverable.

The requested D capability is provided through two non-authoritative layers:

1. A generated `WorkflowExecutorSimulator` exercises dispatch, duplicate,
   timeout, stale lease, cancellation, revocation, late result, and outage
   behavior without an external dependency.
2. A future `WorkflowDispatchAdapter` may submit and observe bounded execution
   intents in an external engine.

An external engine cannot become the source of business truth, approve a
provider, change purpose or fields, resolve a secret, select a destination,
confirm a candidate, activate an alert, bypass review, or override revocation.
It receives opaque job/attempt references and minimized execution parameters,
not raw provider values or credentials. Every callback is authenticated,
idempotent, version-bound, and accepted only while the canonical lease and
provider policy remain valid.

No external engine dependency, service, credential, container, connection, or
deployment is authorized in P4.4 planning or the initial generated tier.

## D-P4.4-007: Deterministic Candidate Evidence

Option A is selected as written. Each requested field uses a versioned
normalizer and comparator and produces exact, compatible, approximate, missing,
stale, invalid, or contradicting evidence. Ranking is bounded and deterministic
with visible ties, top-K limits, minimum-evidence requirements, and explicit
`no_match`, `ambiguous`, and `abstain` outcomes.

Generated calibration can test the machinery but cannot select operational
thresholds. Candidate output always retains `identity_state=not_established`
until a separately authorized human process decides what the evidence means.

## D-P4.4-008: Two Default-Off Entry Lanes

Option C combines manual generated queries with generated hypothesis
enrichment. The lanes have separate switches, budgets, purposes, field
allowlists, audit actions, and kill switches. Enabling one cannot enable the
other.

Hypothesis enrichment may propose a bounded query and attach minimized
candidate evidence to a generated hypothesis revision. It cannot confirm an
identity, mutate immutable source evidence, change a P4.3 lifecycle state,
notify, dispatch, or enforce.

## D-P4.4-009: Versioned Governance And Revocation

Option A is selected as written. Provider definitions progress through explicit
draft, validated-generated, approved-disabled, and future separately authorized
states. Activation never follows automatically from deployment or
configuration presence.

Hierarchical organization, department, provider, provider-version, operation,
purpose, auth-profile, and emergency kill switches block new work and retries,
cancel queued jobs, reject stale leases, quarantine late results, and prevent
cached data from being treated as fresh. History remains append-only.

## D-P4.4-010: Zero Raw Retention And Split Telemetry

Option A is selected as written. Transport bytes exist only inside a bounded
attempt, are parsed under size/depth/item limits, and are discarded. Durable
records contain only allowlisted normalized fields, stable fingerprints,
field-specific evidence, policy/provenance references, and sanitized reason
codes.

Metrics remain low-cardinality and contain no provider values, queries,
candidates, destinations, secret references, users, or camera identifiers.
Audit retains attributable control decisions without storing raw response or
secret material. Canary tests must prove redaction before formatting.

## Reconciled Architecture

```text
Immutable provider manifest + provider-specific adapter
    -> shared typed integration kernel
       -> exact destination and trust policy
       -> closed auth profile + one-attempt secret lease
          -> default unconfigured/generated provider
          -> future disabled encrypted-envelope backend
          -> future constrained auth-profile extension
       -> bounded transport and hostile-response parser
       -> normalized catalogue snapshot + freshness
       -> durable PostgreSQL query job and internal worker
          -> generated workflow-executor simulator
          -> future disabled WorkflowDispatchAdapter
       -> deterministic field evidence + contradiction + abstention
       -> mandatory human review
       -> minimized evidence, audit, telemetry, and revocation
```

## Initial Generated Tier

The first separately authorized implementation slice should include contracts,
compilers, generated providers, generated catalogues, generated query jobs,
generated matching/review fixtures, generated workflow-executor behavior,
revocation, and security tests. It should define but not activate the optional
database-envelope and auth/workflow extension contracts.

The initial tier has no real credentials, no external provider, no external
workflow engine, no network, no Government/private data, no camera/media path,
and no operational action.

## Remaining Gate

The ten owner decisions are complete for planning. The non-effective,
digest-bound `P4.4-PLANNING-R1` package is prepared for exact owner acceptance.
The owner must separately accept its exact SHA-256 before a non-effective
`P4.4-START-R0` package may be prepared. Implementation cannot begin until that
later start package is also accepted exactly.
