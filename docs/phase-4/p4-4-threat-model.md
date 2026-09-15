# P4.4 Authorized Reference Integrations Threat Model

Status date: 2026-09-05

Status: planning only. The model covers a future generated provider and a
future-gated real-provider architecture. It does not authorize implementation,
network access, credentials, real provider configuration, or real data.

## Safety Objective

P4.4 must demonstrate that H-CAM can cross-reference generated observations
against a generated reference catalogue without allowing integration
configuration, provider responses, candidate scores, or system availability to
change identity, alert authority, dispatch, or enforcement decisions.

The generated provider must remain non-issuable, generated-only, default-off,
production-forbidden, department-scoped, purpose-bound, field-minimized,
bounded, attributable, revocable, and fully reconstructable.

## Protected Assets

- provider identity, lifecycle, version, owner, policy, and approval history;
- exact destination and trust-policy definitions;
- opaque secret references and future secret-provider isolation;
- purpose, operation, field, freshness, retention, and cost policy;
- query intent, canonical identity, attempts, receipts, and terminal state;
- generated catalogue records and immutable snapshot lineage;
- normalized candidate sets, per-signal evidence, contradiction, and abstention;
- department isolation and attributable human-review records;
- audit, transactional outbox, provenance, and integrity digests;
- global/provider/department/operation/purpose kill-switch state;
- the boundary preventing real data, operational action, and arbitrary egress.

## Trust Boundaries

1. An authenticated H-CAM actor or internal generated workflow submits a typed
   query intent to the P4.4 policy boundary.
2. Provider, purpose, field, destination, auth, freshness, and budget policies
   compile into an immutable query plan.
3. A query worker claims a durable job under bounded lease and retry rules.
4. A typed adapter maps the query plan to a generated provider operation.
5. A generated in-process provider, or separately authorized loopback
   simulator, returns hostile-by-default structured data.
6. Response validation and minimization produce normalized generated records;
   raw provider material crosses no durable boundary.
7. The deterministic matcher creates a bounded candidate set with per-signal
   evidence, contradiction, freshness, and abstention.
8. A P4.1 hypothesis may reference an accepted generated candidate set, but no
   candidate establishes identity and P4.3 mandatory review remains unchanged.
9. Application department checks and PostgreSQL forced row security form
   separate isolation layers.
10. Audit/outbox/provenance and telemetry receive sanitized metadata only.
11. A future secret provider and future network transport are distinct trust
   boundaries that remain absent in the generated baseline.

## Threats And Required Controls

### Provider-profile confusion

Threat: a generated profile is relabeled as a real provider, one provider uses
another provider's schema/auth/destination, or an old version is executed after
policy changes.

Controls: immutable provider version; generated/real authority class encoded in
the type; provider-kind allowlist; operation, schema, destination, auth,
purpose, field, freshness, retention, and budget digests bound into one
compiled plan; compare-and-swap lifecycle; no mutable inheritance; exact
adapter capability manifest; version revalidation before claim and before
result commit.

### Generic connector becomes arbitrary egress

Threat: a URL, redirect, DNS answer, proxy setting, alternate IP, path,
userinfo component, encoded host, or response-controlled locator sends H-CAM to
an unauthorized destination.

Controls: no URL in query/API payloads; exact compiled scheme, service identity,
port, address policy, path template, method, and query-key allowlist; canonical
URI parsing; no userinfo, fragments, wildcard hosts, suffix matching, redirects,
environment proxies, or response-driven follow-up locations; validate every
resolved address and every connection; require deployment egress controls for
any future real provider.

### TLS or service-identity downgrade

Threat: encryption is present but H-CAM authenticates the wrong service, trusts
an unapproved CA, accepts an expired certificate, or permits verification to be
disabled.

Controls: verified HTTPS; RFC 9525 service-identity policy; RFC 9325 protocol
baseline; exact trust-profile reference; private CA bundle by immutable
reference; certificate and hostname errors are terminal; no insecure toggle;
HTTP permitted only for a separately authorized generated loopback simulator
outside production.

### Credential theft or cross-provider replay

Threat: credentials are hardcoded, cached indefinitely, logged, attached to the
wrong provider/host, reused across purposes, or replayed after rotation or
revocation.

Controls: opaque typed secret references; fail-closed provider; per-attempt
resolution; provider/version/auth/operation/purpose/audience binding; shortest
practical lease; sender-constrained or asymmetric profiles when supported;
rotation and revocation state rechecked before use; no credential values in
durable state, APIs, telemetry, exceptions, fixtures, or evidence.

### Secret-provider substitution

Threat: an attacker selects a file, environment variable, arbitrary plugin, or
fallback source as the secret provider.

Controls: closed provider-kind registry; deployment-owned binding; no
request-selectable implementation; no fallback chain; provider capability and
version digest; typed outcome only; generated baseline binds only
`none_generated` and an unconfigured fail-closed provider.

### Purpose or field-policy bypass

Threat: a valid actor requests an unauthorized purpose, broad record, hidden
field, unrestricted search, or uses results beyond the approved purpose.

Controls: purpose code mapped to provider/version/operation; allowlisted query
signals and result fields; server-side field intersection is insufficient, so
any unapproved field request fails; request minimization before adapter and
response minimization before persistence; purpose, policy, actor, department,
and requested projection bound to query identity and audit; no arbitrary query
language or filter.

### Hostile provider response

Threat: malformed JSON, duplicate keys, deep nesting, huge arrays, compressed
bombs, wrong charset/media type, schema confusion, HTML/script, code, SQL,
locators, or hidden sensitive fields enter H-CAM.

Controls: byte limit before decode; bounded decompression ratio; exact media
type and charset; one-document parser; duplicate-key rejection; depth, node,
string, array, candidate, and page limits; closed schema; recursive prohibited-
field policy; canonical normalization; no dynamic object construction,
deserialization, template rendering, or provider-controlled follow-up request;
malformed responses are terminal and never retried automatically.

### Query replay or semantic collision

Threat: duplicate deliveries create repeated provider effects, a query ID is
reused for different material, or equivalent requests evade deduplication.

Controls: separate delivery idempotency and semantic query keys; canonical
request material; provider/version/department/purpose/operation/field/freshness
policy binding; unique constraints; collision denial; attempt identity; safe-
method/idempotency declaration; append-only correction rather than overwrite.

### Cache poisoning or stale-data laundering

Threat: an old, partial, failed, or differently scoped result is returned as
fresh; stale evidence confirms a match; negative cache hides a new result; a
cache entry crosses departments or policy versions.

Controls: minimized normalized cache only; immutable key includes department,
provider/version, purpose, operation, projection, canonical query digest, and
policy versions; explicit provider/effective/receive/fresh/stale/expiry times;
separate bounded negative-cache policy; visible stale state; stale cannot
satisfy freshness-required behavior or confirm identity; revocation invalidates
active use without deleting audit history.

### False or opaque candidate match

Threat: one approximate value, missing evidence, source staleness, a large
candidate pool, or an opaque combined score is interpreted as identity.

Controls: field-specific normalization; separate exact/approximate/missing/
stale/contradicting outcomes; bounded per-signal contribution; minimum required
signals; top-candidate separation; deterministic tie handling; explicit
abstention; generated calibration version and limitations; no candidate value
establishes identity; mandatory attributable human review; no direct alert
confirmation or action.

### Synthetic data overlaps a real identifier

Threat: a generated fixture accidentally resembles an issuable plate, person
identifier, case, owner, or Government record and is later mistaken for real
data.

Controls: reserved generated namespace; non-issuable formats; generated markers
at record, field, snapshot, query, and candidate-set levels; manifest scanner
for prohibited/realistic identifier formats; no imported datasets; deterministic
seed and generator version; generated-only database constraints; production
startup denial; no sample copied from documentation or websites.

### Cross-department disclosure

Threat: query dedupe, cache, candidates, health, metrics, or worker claims leak
records between departments.

Controls: department in every durable key and relationship; application scope
checks; forced PostgreSQL RLS; non-owner/non-`BYPASSRLS` runtime role; worker
scope set transactionally; no global candidate search; same-department
references; direct SQL and API negative tests; identifiers excluded from metric
labels.

### Unbounded resource or provider-cost consumption

Threat: broad queries, pages, fan-out, retries, concurrent workers, oversized
responses, expensive matching, or repeated operator actions exhaust local or
future provider resources.

Controls: per-query byte/result/page/deadline/match-operation ceilings;
per-provider, department, purpose, and global queue/concurrency/rate/cost
budgets; no open-ended pagination; bounded candidate top-K; deterministic
degradation; budget denial is recorded; no retry storm; no automatic widening;
future provider spending limits remain an operational prerequisite.

### Retry duplicates a non-idempotent effect

Threat: an uncertain response causes a write-like provider operation to execute
twice.

Controls: generated baseline is read-only; operation capability declares safe,
idempotent, idempotency-key-supported, or non-retryable; no automatic retry of
non-idempotent operations; retry only allowlisted transient outcomes; attempts
are bounded and jittered; `Retry-After` is capped by local policy; authorization,
policy, destination, TLS, auth, schema, malformed, and revocation failures do
not retry.

### Circuit breaker hides required evidence

Threat: an open circuit silently returns old candidates, or per-node circuit
state causes inconsistent behavior.

Controls: durable provider/version/operation circuit state; explicit open,
half-open, and closed transitions; lease for bounded probes; stale advisory only
when policy permits; no silent fallback to another provider; candidate set
records degraded source state; health state cannot alter match or review
authority.

### Revocation race or incomplete kill switch

Threat: queued/retrying/in-flight work survives revocation, cached results
continue to appear fresh, or one worker ignores a local kill switch.

Controls: durable hierarchical switch version; check before queue, claim,
secret resolution, transport, normalization, matching, and commit; revocation
transaction records provider revision, cancels unstarted work, blocks retries,
marks cache inactive for new decisions, and emits audit/outbox; in-flight
completion is quarantined if switch/version changed; recovery drill proves no
new terminal candidate after the revocation barrier.

### Audit, error, or provenance leakage

Threat: raw query/candidate/provider values, destinations, secret references,
headers, tokens, or exceptions enter logs, traces, metrics, Problem Details,
outbox headers, or evidence packages.

Controls: safe bounded reason-code taxonomy; allowlisted structured metadata;
no raw stdout/stderr retention from future adapters; redaction before formatting;
separate protected audit from low-cardinality telemetry; sanitized exception
mapping; no values in metric labels; provenance stores digests and typed
activities rather than raw material; generated canary-secret tests.

### Authority escalation into P4.3

Threat: a provider match automatically confirms an alert, establishes identity,
changes severity/priority, or triggers notification, dispatch, or enforcement.

Controls: P4.4 emits only generated candidate-set and evidence-revision records;
`identity_state=not_established`; P4.1/P4.3 accept references through existing
typed contracts; P4.3 remains mandatory-review; no P4.4 port for lifecycle
mutation or external action; cross-module source checks and negative tests.

### Supply-chain or plugin substitution

Threat: a provider adapter imports a new package, dynamically loads code, or
executes provider-supplied schemas/templates.

Controls: closed static adapter registry; no entry-point or path loading;
dependency changes separately reviewed; lockfile/SBOM/vulnerability evidence;
no dynamic code, SQL, template, or schema execution; generated provider uses
existing standard/runtime facilities unless a later package explicitly
authorizes a dependency.

## Abuse Cases

- submit a URL, host, IP, header, cookie, token, certificate, SQL, or code as a
  query field;
- encode an internal or link-local address through alternate numeric, IPv6, or
  userinfo syntax;
- return a redirect, DNS change, or response locator to an unauthorized target;
- request all fields under a valid narrow purpose;
- reuse one query ID with different canonical material;
- use different delivery IDs to repeat the same semantic query;
- return duplicate JSON keys, deep objects, huge compressed bodies, too many
  pages, or mixed media types;
- place a credential or realistic identifier in a generated fixture;
- mix records, cache entries, or candidate evidence across departments;
- rank one fuzzy match as confirmed identity;
- conceal contradictory or stale evidence from the reviewer;
- retry a non-idempotent or revoked operation;
- complete an in-flight attempt after its provider or global switch is revoked;
- capture authorization headers or query strings in traces;
- activate provider execution through import, startup side effect, migration,
  test collection, or production configuration;
- use a generated provider profile as a template that becomes real through a
  configuration-only change.

## Mandatory Stop Conditions

Future implementation or validation stops closed if:

- an owner decision is absent, contradictory, or not bound to the package;
- P4.3 acceptance or another immutable predecessor changes unexpectedly;
- any provider version lacks purpose, field, destination, auth, freshness,
  retention, resource, owner, lifecycle, or revocation policy;
- any query can supply an arbitrary destination, operation, schema, credential,
  header, body, or query language;
- a response can bypass pre-decode and post-decode bounds;
- generated records can overlap a valid real identifier namespace;
- a candidate can establish identity or mutate an alert without human review;
- stale, partial, contradictory, or revoked evidence can appear current;
- retries are possible without safe/idempotent semantics;
- a secret can enter durable state or telemetry;
- department isolation differs between application and PostgreSQL policy;
- generated mode can start in production;
- a required generated security, revocation, or recovery test fails;
- implementation requires network, credentials, real data, models, media,
  deployment, dependencies, or remote Git outside a later exact authorization.

## Residual Risk

Generated validation cannot establish that a real provider is lawful,
available, semantically correct, secure, complete, current, representative, or
suitable for police decisions. It cannot calibrate real-world candidate error
rates, validate identity, prove provider authenticity, set operational
retention, or test provider incident response.

Every real provider requires an independent purpose and authority decision,
data classification, contract, exact fields, destination, authentication,
trust bundle, retention, human workflow, security test, operational owner,
incident and revocation procedure, and explicit activation acceptance.
