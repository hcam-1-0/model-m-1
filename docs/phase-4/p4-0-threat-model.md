# P4.0 Threat Model

Status: generated-only control-plane boundary.

| Threat | P4.0 control | Validation |
| --- | --- | --- |
| Identity or biometric inference enters a generic payload | Recursive prohibited-field policy | Parameterized negative tests for every denied field |
| Arbitrary provider destination or credential is supplied | Provider schema contains no destination, URL, secret, token, query schema, or transport input | API extra-field and recursive guardrail tests |
| A draft rule becomes an operational decision | Mandatory-review literal, nonoperational database constraint, runtime absent | Contract, API, database, and source-surface tests |
| Autonomous action is introduced accidentally | Authority guard rejects the future class | Explicit authority-escalation negatives |
| Cross-department records are read or written | Principal filters plus forced PostgreSQL RLS | API isolation and PostgreSQL role test |
| Concurrent update overwrites review state | SQLAlchemy version column and `If-Match` | Missing, malformed, stale, and transition tests |
| Evidence is ambiguous after replay | Canonical JSON, SHA-256 identity, distinct UTC chronology | Canonicalization and chronology tests |
| Oversized or deeply nested input exhausts resources | 64 KiB, depth 16, node 8192, graph/rule cardinality bounds | Boundary negatives |
| A provider record silently becomes active | Status disabled, enabled false, transport absent, credentials none in contract and database | API and constraint tests |
| A change is not attributable | Typed actor, reason, audit event, and unpublished transactional outbox event | API persistence assertions |
| Sensitive data leaks through responses | Typed response models and no-store headers | OpenAPI, API, and header tests |
| Production enables generated control-plane mutation | Configuration constructor rejects the flag in production | Settings negative test |

## Trust Boundaries

The browser or API caller is untrusted. Pydantic validation and the recursive
guardrail form the input boundary. Application authorization is the first
department boundary; PostgreSQL forced RLS is the defense-in-depth boundary.
Canonical documents and database constraints form the durable-record boundary.

No network provider, camera, media, model, dataset, inference runtime,
notification service, or deployment environment is inside the P4.0 trust
boundary. References to those capabilities are future contracts only.

## Residual Risk

P4.0 does not prove operational correctness because it cannot operate. The
generated contracts require future legal, privacy, data-governance, model,
provider, human-factors, and deployment reviews. PostgreSQL table owners,
superusers, and `BYPASSRLS` roles remain privileged infrastructure identities;
product roles must never receive those privileges. SHA-256 provides integrity
identity, not legal authenticity or evidentiary admissibility.
