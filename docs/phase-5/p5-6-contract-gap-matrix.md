# P5.6 Contract And Producer Gap Matrix

Status date: 2026-09-10

Status: 48 producer gaps preserved; no backend work authorized

## Reading Rule

`available` means an accepted bounded contract or generated producer can inform
the UI. It does not mean a production producer, deployment, or operational
authority exists. `gap` means P5.6 must render an explicit unavailable,
unknown, stale, partial, or non-effective state rather than fabricate data or
behavior.

## Existing Foundations

- accepted Phase 5 shell, navigation, sessions, capability ceiling, query,
  error, observability, and resource-profile packages;
- accepted P5.3 Operations camera/live surfaces using generated media only;
- accepted Phase 2 camera, stream, capability, ETag, audit, and department
  boundaries;
- accepted Phase 3 analytics assignments, runtime profile, model-lane, and
  dynamic capability contracts under default-off safety gates;
- accepted Phase 4.6 operations contracts and read endpoints for objectives,
  budgets, degradation, controls, recovery, capacity, supply chain, and
  security evidence;
- PostgreSQL/PostGIS RLS patterns and generated validation in accepted phases;
- P4.7 Phase 5 handoff contracts and explicit production prerequisites.

## Gap Matrix

| ID | Required producer or contract | Existing state | P5.6 planning response |
| --- | --- | --- | --- |
| P5.6-G01 | Organization list/detail with hierarchy and status | No authoritative operator API | Generated projection; mutations unavailable |
| P5.6-G02 | Department list/detail, ownership, lifecycle, and policy revision | Department scope exists in domain records, no complete administration API | Generated bounded hierarchy and detail |
| P5.6-G03 | User/account list/detail with minimized fields | Auth/session projection exists, no user-management producer | Opaque synthetic identities only |
| P5.6-G04 | Department membership revision and history | No complete producer | Generated append-only revision history |
| P5.6-G05 | Role catalogue, hierarchy, and revision history | Capabilities exist, no role-governance API | Generated role projections |
| P5.6-G06 | Permission/capability catalogue and resource-action matrix | Capability ceiling exists but not enterprise administration | Generated server-shaped matrix; no client inference |
| P5.6-G07 | Static and dynamic separation-of-duty policy | No authoritative producer | Generated conflicts and unavailable execution |
| P5.6-G08 | Access-review campaign, assignment, decision, and expiry | No producer | Generated review queue and receipts |
| P5.6-G09 | Identity-provider and federation inventory/health | No producer | Metadata-only disabled projection |
| P5.6-G10 | Session inventory, assurance, reauthentication, and revocation propagation | Session projection is client-facing but no administration aggregate | Generated minimized posture only |
| P5.6-G11 | Policy catalogue, revision, compile/validation, and effective state | Domain policies exist in separate modules, no unified governance API | Typed generated policy records |
| P5.6-G12 | Server-authoritative RBAC plus contextual ABAC decision explanation | Capability responses exist, no unified explain producer | Generated safe explanation; no browser evaluation |
| P5.6-G13 | Administrative change-request lifecycle | No reusable cross-domain producer | Generated draft/validate/review lifecycle |
| P5.6-G14 | Approval eligibility and SoD decision | No producer | Generated eligibility; fail closed |
| P5.6-G15 | Step-up/reauthentication challenge and completion | No producer | Required/unavailable state only |
| P5.6-G16 | Effective change executor, schedule, rollback, and result | No executor | Explicitly non-effective; no apply action |
| P5.6-G17 | Organization-wide camera/stream governance aggregate | Camera and stream APIs exist; unified admin aggregate absent | Generated aggregate with links to accepted APIs |
| P5.6-G18 | Integration/provider catalogue and governance lifecycle | P4.4 typed generated reference integration contracts exist | Generated metadata; real providers unavailable |
| P5.6-G19 | Destination-policy inventory and effective validation state | Exact destination controls exist in isolated contracts | Generated sanitized rule projection only |
| P5.6-G20 | Secret-reference provider metadata, rotation, and access review | Typed `secret_ref` exists; no operator governance producer | Opaque refs and unavailable secret operations |
| P5.6-G21 | Feature-flag catalogue, typed values, evaluation details, and history | No platform feature-control producer | Generated typed projections; no SDK/provider |
| P5.6-G22 | Configuration catalogue, schemas, dependencies, and revision history | Domain configuration is fragmented | Generated bounded catalogue; no generic editor |
| P5.6-G23 | Blast-radius and dependency impact evaluator | No producer | Deterministic generated impact projection |
| P5.6-G24 | Kill-switch list/detail/history and authoritative effective state | P4.6 `KillSwitchRevisionV1` exists, no complete UI-specific API | Consume generated/read projection; no toggle |
| P5.6-G25 | Model-lane governance, artifact eligibility, and assignment impact | Phase 3 contracts exist, no P5.6 producer | Generated/default-off projection; no model action |
| P5.6-G26 | Resource-profile catalogue, observed capability, and eligibility | Phase 3/P5 resource profiles exist | Reuse profiles; generated observed state only |
| P5.6-G27 | Deployment-profile catalogue and desired-state topology | P4.6 platform-neutral projections exist | Generated standalone/GPU/server/Kubernetes views |
| P5.6-G28 | Retention-policy catalogue, jurisdiction refs, and effective state | P4.5 non-operative policy contracts exist | Generated policy previews; no period decision |
| P5.6-G29 | Administrative event stream and authoritative history | Domain audit/outbox records exist, no unified admin event producer | Generated typed events with source refs |
| P5.6-G30 | Immutable audit list/detail/query API | Audit records exist across modules, no bounded enterprise explorer | Generated references; no universal raw search |
| P5.6-G31 | Security-event list/detail and denial aggregates | P4.6 security evidence exists, no complete event producer | Generated low-cardinality aggregates and refs |
| P5.6-G32 | API authorization and PostgreSQL RLS parity evidence | RLS tests exist by phase, no operational evidence feed | Generated assurance records with explicit scope |
| P5.6-G33 | Privileged-access, wildcard, dormant, and escalation findings | No producer | Generated findings; no security conclusion |
| P5.6-G34 | Compliance framework/control mapping and policy evidence | No unified producer | Generated references; no compliance claim |
| P5.6-G35 | Exception lifecycle, approval, expiry, and compensating controls | No producer | Generated non-effective workflow |
| P5.6-G36 | Attestation lifecycle and evidence references | Phase evidence exists, no operational attestation API | Generated references; no evidence resolution |
| P5.6-G37 | Dependency/SBOM/license/vulnerability/provenance query API | P4.6 `SupplyChainInventoryV1` and evidence exist | Generated/read projection with freshness and unknowns |
| P5.6-G38 | Vulnerability refresh, applicability, and exception producer | Refresh not available; prior limitations explicit | Show stale/not-run; no scanner action |
| P5.6-G39 | Platform service inventory and dependency topology | P4.6 registry/contracts exist but no complete UI producer | Generated/read projection with authoritative table |
| P5.6-G40 | Low-cardinality health, SLI, SLO, budget, and degradation query API | P4.6 read views exist | Reuse accepted reads; no production target claims |
| P5.6-G41 | Queue, worker, lease, retry, dead-letter, circuit, and recovery API | P4.6 contracts exist, operational producer absent | Generated bounded operations projection |
| P5.6-G42 | Database, storage, event-bus, media-edge, and cache status API | No consolidated producer | Generated component status; no underlying data access |
| P5.6-G43 | AI runtime, scheduler, saturation, bypass, and profile status API | Phase 3 runtime contracts exist, no operational producer | Generated/default-off status only |
| P5.6-G44 | Backup inventory, restore evidence, and recovery-drill history | P4.6 recovery contracts exist; execution absent | Generated history and unknown limitations |
| P5.6-G45 | Maintenance proposal, approval, schedule, and result | No producer/executor | Generated non-effective workflow |
| P5.6-G46 | C1/C10/C50 capacity-result query with hardware and workload identity | P4.6 generated capacity contracts exist | Reuse generated evidence; no production extrapolation |
| P5.6-G47 | Per-domain event invalidation and authoritative HTTP confirmation | Shared invalidation pattern exists, P5.6 topics absent | Plan typed topic map and refetch contract |
| P5.6-G48 | Portal saved views, table preferences, multi-monitor layouts, and revisioned profile | Shared UI profile concepts exist, no server producer | Local generated projection only; no security context stored |

## Gap Classes

| Class | IDs | Count |
| --- | --- | ---: |
| Organization, identity, role, and session | G01-G10 | 10 |
| Policy, change, and approval | G11-G16 | 6 |
| Resource, provider, feature, profile, and retention governance | G17-G28 | 12 |
| Audit, security, compliance, and supply chain | G29-G38 | 10 |
| Operations, recovery, capacity, events, and preferences | G39-G48 | 10 |
| Total | G01-G48 | 48 |

## Required Failure Behavior

For every gap, the UI must:

- identify the missing producer or unsupported operation;
- preserve the page and workflow using generated or explicit unavailable
  state when authorized by the future start package;
- avoid guessing effective policy, authority, health, security, compliance,
  freshness, or execution outcome;
- never substitute direct browser access to a database, provider, camera,
  model, broker, telemetry backend, secret store, scanner, cluster, or host;
- retain authoritative tables and safe typed errors;
- keep proposed actions non-effective until a separately authorized producer,
  enforcement path, validation package, and owner gate exist.

## Producer Sequencing Recommendation

After the generated-only UI contract milestone, future backend delivery should
prioritize:

1. organization, department, role, and capability reads;
2. policy explanation and administrative change/approval contracts;
3. bounded audit, security, and P4.6 operations queries;
4. feature/config/provider/secret-reference governance reads;
5. maintenance, recovery, retention, and deployment previews;
6. separately authorized mutation/executor paths only after threat, audit,
   rollback, SoD, and production controls are independently accepted.

No item in this sequence is authorized by this planning record.
