# P4.4 Authorized Reference Integrations Research Record

Status date: 2026-09-05

Status: official primary-source research and repository analysis complete for
planning. No product implementation, provider connection, credential or secret
access, Sentinel access, external network validation, Government/private data,
camera/media access, model or dataset work, operational action, container,
Kubernetes, deployment, or remote Git action is authorized.

## Research Question

P4.4 must prove that H-CAM can safely express and test a reference-data
integration without turning a generic connector into an authorization bypass.
It must support generated provider records, bounded queries, explicit freshness,
explainable multi-signal candidate ranking, contradiction, abstention, and human
review while preserving the accepted no-identity and non-operational boundary.

The research addressed provider composition, destination and transport policy,
authentication and secret references, request/response validation, retry and
freshness semantics, data minimization, provenance, candidate review,
observability, revocation, and generated-only validation.

## Existing H-CAM Baseline

P4.0 already created `ReferenceProviderV1` and `ReferenceQueryV1`, persistence,
department-scoped APIs, forced PostgreSQL row-security definitions, canonical
digests, audit records, and transactional outbox events. Those contracts are
intentionally inert:

- provider kind is only `generated_fixture`;
- provider status is `disabled` and `enabled` is false;
- transport state is `absent` and credential state is `none`;
- every query is stored as `blocked/provider_disabled`;
- arbitrary URLs, query languages, credentials, provider payloads, owner data,
  watchlist identity, and biometric fields are rejected;
- runtime remains default-off and forbidden in production.

P4.4 should version and extend this boundary. It must not create a second
provider registry or weaken the P4.0 constraints in place. Any future real
provider remains a separately authorized provider profile, not a configuration
change to the generated provider.

## Findings

### 1. Provider configuration must compile into an immutable capability

The [OpenAPI 3.2.0 specification](https://spec.openapis.org/oas/v3.2.0.html)
describes machine-readable API interfaces, but also warns that external
references may be dereferenced automatically, reference cycles can exhaust
resources, and rich text can require sanitization. H-CAM must therefore never
accept a provider-supplied OpenAPI document as executable runtime
configuration.

The planned boundary is an H-CAM-owned, versioned provider manifest. It binds a
closed adapter kind, enumerated operation keys, request and response schema
digests, purpose policy, field projection, auth profile reference, destination
policy digest, freshness policy, resource budgets, retention class, lifecycle,
and owner. A deterministic compiler turns an accepted manifest into an
immutable execution plan. Unknown operations, runtime URLs, remote references,
and unbounded schemas fail closed.

P4.4 may use OpenAPI only as a documentation/export projection. The accepted
H-CAM contract remains authoritative, and no OpenAPI conformance claim is made.

### 2. A generic transport is a mechanism, not permission

The [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
and [OWASP API7:2023](https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/)
identify server-controlled outbound requests and unsafe URL handling as SSRF
risk. [OWASP API10:2023](https://owasp.org/API-Security/editions/2023/en/0xaa-unsafe-consumption-of-apis/)
also calls out blind redirects, weak transport validation, missing timeouts,
oversized third-party responses, and trusting integrated APIs more than user
input.

H-CAM should separate four decisions:

1. the provider version authorizes a named operation;
2. a destination policy authorizes an exact route;
3. an auth profile authorizes one credential mechanism;
4. the transport only executes the already compiled request plan.

The transport cannot accept a user URL, hostname suffix, arbitrary method,
query string, header, body schema, proxy, redirect, or credential. Real
deployment would additionally require network-layer egress enforcement. An
application allowlist alone is not a sufficient production boundary.

### 3. TLS verification requires service identity, not encryption alone

[RFC 9325 / BCP 195](https://www.rfc-editor.org/rfc/rfc9325.html) provides
current secure TLS/DTLS recommendations, while
[RFC 9525](https://www.rfc-editor.org/rfc/rfc9525.html) defines service identity
verification for TLS. P4.4 should require verified HTTPS for any future
non-loopback provider, a provider-bound trust profile, exact expected service
identity, and no certificate-verification disable switch.

Private certificate authorities may be referenced by an approved trust-bundle
identifier. The plan does not recommend universal certificate pinning because
incorrect pin lifecycle can break rotation. A provider-specific profile may
later require public-key or certificate constraints after operational review.

HTTP is limited to an explicitly authorized generated loopback simulator in a
non-production environment. Redirect following and environment proxies remain
off. DNS answers and every connection target must be revalidated against the
compiled destination policy to address rebinding and multi-address behavior.

### 4. Authentication must be typed and provider-specific

[RFC 9700 / BCP 240](https://www.rfc-editor.org/rfc/rfc9700.html) recommends
strong OAuth client authentication, sender-constrained tokens where applicable,
and end-to-end TLS. [RFC 8705](https://www.rfc-editor.org/rfc/rfc8705.html)
defines OAuth mutual-TLS client authentication and certificate-bound tokens.
[RFC 9421](https://www.rfc-editor.org/rfc/rfc9421.html) defines HTTP message
signatures but requires each application profile to specify covered components
and signature parameters.

P4.4 should define a closed auth profile union rather than a free-form header
map. Planned future profile types are:

- `none_generated`, valid only for the generated in-process provider and an
  explicitly authorized loopback simulator;
- `api_key_header`, with a fixed provider-defined header name and secret
  reference;
- `oauth2_client_credentials`, with exact issuer/token endpoint metadata and
  scoped audience;
- `oauth2_mtls` or `mutual_tls`, with certificate/key references and identity
  policy;
- `private_key_jwt`, where provider capability requires it;
- `http_message_signature`, only through a provider-specific RFC 9421 profile.

This is a capability catalogue, not authorization to implement all modes. The
generated-only baseline implements no real credentials.

### 5. Secret references must resolve per attempt and remain non-observable

The [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
recommends centralized secret storage, access control, auditing, lifecycle, and
rotation rather than hardcoded or scattered credentials.

The planned `ReferenceSecretProvider` returns a bounded short-lived secret
lease or cryptographic handle for an exact provider version, auth profile,
operation, and purpose. Resolution occurs for each attempt so rotation does not
require a worker restart. Application records store only an opaque secret
reference, provider type, version, and safe resolution outcome.

Secret values, token endpoints containing credentials, authorization headers,
certificates, private keys, signed request material, and provider response
fragments are forbidden from APIs, database rows, audit, outbox events,
metrics, traces, logs, exceptions, fixtures, and evidence packages. The default
provider is unconfigured and fails closed. Generated validation uses
non-secret sentinel objects designed to fail if stringified.

### 6. Requests and responses are hostile structured input

[JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12) supplies
closed validation vocabulary, including bounded arrays/strings and control of
unevaluated properties. H-CAM should continue using executable Pydantic
contracts as the product boundary and emit deterministic JSON Schema snapshots
for review.

Each operation has separate input, provider-request, provider-response, and
normalized-result contracts. Bounds apply before parsing where possible and
again after decoding. Requirements include byte ceilings, depth/node/array/
string limits, media-type allowlists, charset handling, decompression ratio,
single-document parsing, duplicate-key policy, unknown-field denial, canonical
normalization, and safe failure codes.

Provider responses do not become trusted because they passed TLS or came from a
Government domain. They cannot introduce a destination, query, credential,
identity assertion, code, SQL, URL, media locator, or downstream command.

### 7. Resource budgets and retries are part of the security contract

[OWASP API4:2023](https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/)
recommends explicit limits on execution time, memory, process/file resources,
payload size, operation count, page size, interaction rate, and provider cost.
[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) distinguishes idempotent
methods and warns against automatically retrying non-idempotent requests unless
the client can prove equivalent semantics.

P4.4 should use database-backed query jobs with semantic query identity,
attempt identity, bounded leases, per-provider and per-department concurrency,
request/response size limits, deadlines, page/result ceilings, and cost units.
Only transport-unavailable, timeout-before-response, explicit rate-limit, and
selected 5xx outcomes may retry, and only when the operation is declared safe
or has a provider idempotency contract. Policy, auth, destination, TLS,
validation, revocation, and malformed-response failures do not retry.

### 8. Freshness is a first-class evidence property

[RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html) distinguishes fresh and
stale responses and does not generally permit stale use without explicit
authorization. [RFC 5861](https://www.rfc-editor.org/rfc/rfc5861.html) provides
bounded `stale-while-revalidate` and `stale-if-error` concepts.

H-CAM should not blindly inherit provider cache headers. A provider-specific
freshness policy determines `observed_at`, `provider_effective_at`,
`received_at`, `fresh_until`, `stale_until`, and `expired_at`. A stale result
may be visible as clearly stale advisory evidence only when policy permits; it
cannot confirm a match, satisfy a freshness-required rule, or silently replace
a failed query. Expired results are unavailable for decision support.

Cache keys bind department, provider version, purpose, operation, requested
field projection, normalized query digest, and policy versions. Negative cache
entries have a separate short policy. Raw responses are never the cache value.

### 9. Data minimization is enforced before and after transport

The [NIST Privacy Framework](https://www.nist.gov/privacy-framework) treats
privacy across the data lifecycle and relationships between data-processing
entities. [NIST SP 800-63C](https://pages.nist.gov/800-63-4/sp800-63c.html)
illustrates requesting only needed attributes and preferring derived answers
where a full value is unnecessary. The
[W3C Privacy Principles](https://www.w3.org/TR/privacy-principles/) similarly
recommend minimizing API transfers.

P4.4 therefore needs both request and response minimization. A purpose policy
maps a named operation to the smallest allowed query signals and result fields.
The adapter cannot request a superset for convenience. Normalization discards
unapproved fields before persistence, caching, audit, matching, or downstream
events. Where possible, generated validation uses derived assertions such as
`attribute_consistent=true` rather than full attributes.

The [Government of India Open API Policy](https://www.meity.gov.in/static/uploads/2024/03/Policy-Document.pdf)
supports interoperable, machine-readable and safely shared Government APIs,
but it does not grant H-CAM access to any provider or data. Provider authority,
classification, purpose, fields, credentials, retention, and incident response
remain separate organizational gates.

### 10. Candidate ranking cannot establish identity

The [NIST AI RMF 1.0](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf)
calls for context-specific validity and reliability, documented test sets and
methods, defined human-oversight processes, explicit thresholds, safe failure
beyond knowledge limits, and documented limitations.

P4.4 uses no model. Its planned generated matcher is deterministic and
field-specific. It reports each exact, normalized, approximate, missing,
stale, and contradicting signal separately; produces bounded candidate ranks;
records policy/version lineage; and can abstain. A combined ranking value is a
queue aid, not probability, identity, guilt, threat, or authority.

Synthetic calibration proves implementation behavior only. It cannot establish
operational thresholds, real-world error rates, fairness, or suitability.
Every candidate set remains `identity_state=not_established` and requires an
attributable human review before it can contribute to a police-intelligence
hypothesis or alert disposition.

### 11. Provenance must be useful without becoming a leakage channel

The [W3C PROV overview](https://www.w3.org/TR/prov-overview/) describes entities,
activities, agents, and derivations for assessing quality, reliability, and
trustworthiness. [PROV-AQ](https://www.w3.org/TR/prov-aq/) warns that provenance
itself can expose sensitive information and needs access control.

H-CAM should preserve provider version, operation, policy digests, request
digest, response receipt digest, normalization activity, matching-policy
version, candidate-set digest, chronology, and service actor. It must not put
query values, candidate values, secret references, destinations, raw provider
material, or identifiers into public provenance, metrics, or outbox headers.
H-CAM uses W3C-inspired semantics without claiming formal PROV conformance.

### 12. Revocation must stop new work and make old evidence visibly historical

Provider lifecycle and runtime health are different. A provider can be
administratively approved but temporarily degraded, or technically healthy but
revoked. Planned administrative states are `draft`, `validated`,
`approved_generated`, `enabled_generated`, `suspended`, `revoked`, and
`retired`. Real-provider states remain unavailable under Tier A.

Revocation atomically blocks new claims, prevents retries, invalidates cached
freshness for active use, cancels unstarted work, requests cancellation of
bounded in-flight work, records an attributable revision/audit/outbox event,
and retains historical evidence according to policy. It does not erase prior
review history. Global, provider, department, operation, and purpose kill
switches fail closed.

### 13. Errors and telemetry remain bounded and non-sensitive

[RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) provides typed Problem
Details for HTTP APIs and cautions against exposing debugging information in
human-readable detail. Planned errors use stable safe codes for policy,
destination, auth, TLS, timeout, rate, response, freshness, circuit,
revocation, ambiguity, contradiction, and abstention outcomes.

The [OpenTelemetry HTTP semantic conventions 1.44.0](https://opentelemetry.io/docs/specs/semconv/http/)
include HTTP client concepts and warn that URLs, query strings, and headers may
contain sensitive material. P4.4 should pin its adopted mapping and use only
low-cardinality labels such as adapter kind, operation class, outcome, attempt
class, freshness state, circuit state, and safe reason code. Provider IDs,
departments, users, query/candidate values, URLs, hostnames, record IDs, secret
references, and digests are not metric labels.

## Planning Conclusions

P4.4 should be designed as a shared typed integration kernel with compiled,
immutable provider profiles and provider-specific adapters. The generated
provider proves the complete policy, query, normalization, matching, review,
revocation, audit, and recovery flow without network access or real data.

The future generic transport is deliberately powerless: it accepts only a
compiled request plan and secret lease produced by separately authorized
policy components. A real provider cannot be enabled merely by adding a URL or
configuration file.

The next planning gate is selection of the owner decisions in
`p4-4-decision-packet.md`. Recommendations are not decisions, and `continue` or
silence cannot accept them. Implementation requires a later reconciled package
and separate exact start authorization.
