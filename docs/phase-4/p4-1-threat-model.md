# P4.1 Generated Correlation Threat Model

Status: generated-only foundation; no operational authorization.

## Protected Properties

P4.1 protects department isolation, deterministic replay, immutable accepted
history, visible failure outcomes, bounded resource use, canonical evidence
provenance, mandatory human authority, and zero expansion into model, media,
provider, rule-activation, alert, dispatch, or deployment behavior.

## Threats And Controls

| Threat | Control | Verification |
|---|---|---|
| Unknown or hostile event enters correlation | Closed typed Phase 3 adapter, forbidden unknown fields, 64 KiB canonical boundary | Ingress and negative contract tests |
| Event crosses camera or department scope | Exact stream/camera resolution plus department validation | Scope tests and PostgreSQL RLS test |
| Duplicate ID hides changed content | Event ID plus canonical digest; same-ID different-digest conflict | Receipt and persistence tests |
| Events disappear during pressure | Explicit capacity, late, gap, skew, conflict, and policy outcomes | Ordering and bounds tests |
| Replay yields a different result under the same ID | Ordered event digests plus profile/configuration and semantic version binding | Exact replay golden tests |
| Optional lane overrides deterministic policy | Required deterministic lane and hard veto during arbitration | Lane and contradiction tests |
| Model code becomes executable early | Optional lanes report `unavailable`; prohibited imports and dependency checks | Static security test and readiness checker |
| Correlation asserts identity, guilt, intent, or risk | Recursive guardrails and constrained generated subject/evidence contracts | Guardrail negative tests |
| Flat projection becomes a second source of truth | Projection is graph-digest-bound and rebuildable | Hypothesis tests |
| Revision rewrites evidence history | Append-only revision rows and immutable evidence references | Persistence revision tests |
| Worker races duplicate a run | Idempotent run digest, bounded leases, PostgreSQL `SKIP LOCKED` | SQLite and PostgreSQL tests |
| Database role bypasses department scope | Application filtering plus forced PostgreSQL RLS | PostgreSQL isolation test |
| Production accidentally enables generated runtime | Settings constructor rejects production enablement | Configuration negative test |
| Application starts hidden background work | No startup worker construction and no public start endpoint | Startup and API-surface tests |
| Metrics leak identifiers or payloads | Fixed low-cardinality outcome labels only | Metrics tests and source scan |

## Trust Boundaries

Phase 3 event records, API callers, profile configuration, optional lane-result
fixtures, and database contents are untrusted inputs. Pydantic validation,
canonicalization, recursive intelligence guardrails, exact scope resolution,
resource bounds, and persistence constraints form successive boundaries.

The deterministic CPU lane and repository-owned generated JSON fixtures are
inside the authorized test boundary. Cameras, media, models, datasets,
artifacts, provider transports, credentials, Government/private data, rule
activation, operational alerts, dispatch, enforcement, Kubernetes, deployment,
and remote Git are outside it.

## Failure Policy

Malformed, oversized, cross-scope, unsupported, future-skewed, over-capacity,
or integrity-conflicting inputs fail closed with typed sanitized reason codes.
Partial or contradictory evidence produces abstention. No failure activates an
operational fallback, optional model lane, provider, rule, alert, or action.

## Residual Risk

P4.1 does not establish operational accuracy, fairness, evidentiary
admissibility, camera compatibility, model performance, or deployment safety.
SQLite cannot prove PostgreSQL concurrency or RLS behavior. PostgreSQL table
owners, superusers, and `BYPASSRLS` roles remain privileged identities and must
never be assigned to product callers. Future operational use requires separate
data governance, legal, privacy, security, human-factors, model, and deployment
gates.
