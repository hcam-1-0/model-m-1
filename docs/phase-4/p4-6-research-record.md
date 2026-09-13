# P4.6 Operations, Security, And Scale Research Record

Status date: 2026-09-05

## Authority And Scope

`D-P4.6-PLAN-AUTH` authorizes read-only repository analysis, official
primary-source research, local planning documentation, document validation,
and one local checkpoint commit without push. This record is planning-only.
It does not authorize implementation, runtime execution, hardware or capacity
testing, backup or restore execution, containers, Kubernetes, operational
network access, data or media, models, deployment, or remote Git.

## Research Questions

1. How should H-CAM expose metrics, traces, logs, audit, security, and evidence
   without mixing purposes or leaking sensitive identifiers?
2. Which SLI, SLO, error-budget, alert, and degradation contracts are useful
   before production targets are known?
3. How should existing domain-owned workers converge on one resilience policy
   while retaining module ownership and transactional truth?
4. How should application authorization and PostgreSQL row security be tested
   as two independent controls?
5. Which supply-chain evidence formats can be supported without making an
   unsupported conformance or security-level claim?
6. What evidence is required before H-CAM can claim backup, restore, recovery,
   capacity, or Kubernetes readiness?
7. How can one codebase degrade safely on a developer laptop and scale to GPU
   laboratories, servers, and Kubernetes without hard-coding one environment?

## Accepted Starting Point

The P4.5 acceptance commit is
`1b54aafc252248eb502cd04ebd2130b0cf1684bf`. Phase 4 is **85/100
(85.00%)** and P4.6 is **0/10 (0.00%)**. Planning earns no Phase 4 points.

The repository already has useful foundations:

| Surface | Existing baseline | P4.6 planning implication |
| --- | --- | --- |
| Metrics | `app/hcam/metrics.py` exposes Prometheus metrics behind a secret-file bearer token | Preserve the endpoint and create a bounded registry rather than replacing it |
| Request context | `app/hcam/observability.py` generates or validates request IDs and emits sanitized access records | Extend to typed trace context without treating a request ID as a trace |
| Domain metrics | Analytics, correlation, rules, alerts, integrations, and investigations own local metric adapters | Standardize names, labels, outcomes, and cardinality centrally while preserving ownership |
| Audit | Append-oriented audit models and repository exist separately from ordinary logs | Keep audit authoritative and prevent trace/log retention from becoming audit retention |
| Authentication | Typed principals, roles, department scopes, and fail-closed authenticators exist | Test application authorization and database RLS as independent oracles |
| Request safety | Body limits and sensitive-response headers are implemented | Add telemetry leak tests and abuse envelopes, not duplicate middleware |
| Workers | Stream, capability, analytics, correlation, integration, alert, and investigation workers already use bounded job patterns | Define a common policy contract and conformance tests; do not centralize all job state |
| Database recovery | SQLite backup verification and recovery drills exist | Preserve them as a developer baseline and plan PostgreSQL restore/PITR evidence separately |
| CI | Unit, coverage, dependency audit, package, container, PostgreSQL/PostGIS, synthetic lab, and recovery jobs exist | Add P4.6 evidence lanes without weakening accepted historical jobs |
| Deployment | Non-root image and Compose files exist | Treat Kubernetes as a future adapter and require static plus owned-cluster evidence before claims |

## Official Primary Sources

### Observability And Reliability

| Source | Relevant primary guidance | Bounded H-CAM implication |
| --- | --- | --- |
| [OpenTelemetry Specification](https://opentelemetry.io/docs/specs/otel/) | Defines vendor-neutral APIs and data models for traces, metrics, logs, resources, context, and protocol export | Define typed OTel-compatible projections and default-off exporters; do not require an OTel backend in P4.6 |
| [OpenTelemetry versioning and stability](https://opentelemetry.io/docs/specs/otel/versioning-and-stability/) | Semantic conventions evolve through schemas and stability levels | Version H-CAM telemetry contracts and pin any implemented semantic-convention projection |
| [W3C Trace Context](https://www.w3.org/TR/trace-context/) | Standardizes `traceparent` and `tracestate` propagation | Validate and forward bounded trace context; never place identity, reason text, secrets, or case data in it |
| [Prometheus metric naming](https://prometheus.io/docs/practices/naming/) | Recommends single units and warns that every label combination creates another series | Keep base units and a closed low-cardinality label registry |
| [Prometheus instrumentation](https://prometheus.io/docs/practices/instrumentation/) | Separates online, offline, and batch service signals and warns against unbounded labels | Define service-class templates and move identifiers to controlled logs/traces, not metric labels |
| [Prometheus alerting](https://prometheus.io/docs/practices/alerting/) | Recommends symptom-based, actionable alerting with slack for transient failures | Separate internal reliability alerts from police intelligence alerts and page only on actionable symptoms |
| [Google SRE service-level objectives](https://sre.google/sre-book/service-level-objectives/) | Defines SLIs, SLOs, and error budgets around user-relevant behavior | Freeze schemas now, but leave production targets unset until measured and owner approved |

Observed on 2026-09-05, the OpenTelemetry specification page identified
version 1.60.0. That version is research context, not a dependency pin. Any
future implementation package must recheck the current stable specification.

### Security, Logging, Incident Response, And Contingency

| Source | Relevant primary guidance | Bounded H-CAM implication |
| --- | --- | --- |
| [NIST SP 800-92](https://csrc.nist.gov/pubs/sp/800/92/final) | Enterprise log-management infrastructure and processes | Separate generation, transport, storage, access, retention, and disposal policies by signal purpose |
| [NIST SP 800-53 Rev. 5 Update 1](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) | Access control, audit, incident response, contingency, integrity, and system-assurance controls | Use control mappings as traceability, not a compliance claim or selected government baseline |
| [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final) | Integrates incident response across CSF 2.0 preparation, detection, response, and recovery | Model security incidents and recovery evidence as a lifecycle, distinct from policing alerts |
| [NIST SP 800-34 Rev. 1](https://csrc.nist.gov/pubs/sp/800/34/r1/upd1/final) | Business-impact analysis, recovery strategies, exercises, and plan maintenance | Require named service tiers, declared RPO/RTO, restore evidence, and lessons learned before resilience claims |
| [NIST SP 800-218 SSDF](https://csrc.nist.gov/pubs/sp/800/218/final) | Secure development practices and common producer/consumer vocabulary | Bind build, dependency, test, review, and vulnerability evidence to exact source and tool versions |
| [NIST SP 800-161 Rev. 1](https://csrc.nist.gov/pubs/sp/800/161/r1/upd1/final) | Multi-level cybersecurity supply-chain risk management | Track supplier, component, provenance, risk, exception, and review state without claiming that an SBOM proves safety |

The 2023 NIST SP 800-92 Rev. 1 page is an initial public draft. This plan uses
the final SP 800-92 as the normative research baseline and treats the draft as
informative only.

### PostgreSQL Concurrency, Isolation, And Recovery

| Source | Relevant primary guidance | Bounded H-CAM implication |
| --- | --- | --- |
| [PostgreSQL 18 row security](https://www.postgresql.org/docs/18/ddl-rowsecurity.html) | Default deny without a policy; superusers and `BYPASSRLS` bypass; owners normally bypass unless forced | Test normal roles, table owner, forced RLS, superuser, `BYPASSRLS`, policy absence, constraints, and race-sensitive policy expressions |
| [PostgreSQL 18 SELECT locking](https://www.postgresql.org/docs/18/sql-select.html) | `SKIP LOCKED` produces an inconsistent view suitable for queue-like consumers, not general queries | Limit it to bounded claims with leases, idempotency, reaping, and durable terminal outcomes |
| [PostgreSQL 18 PITR](https://www.postgresql.org/docs/18/continuous-archiving.html) | Base backups plus WAL archives support point-in-time recovery and warm standby designs | Plan separately controlled PostgreSQL backup profiles; never infer recoverability from backup creation alone |

PostgreSQL 18.6 was the current supported release shown during research. The
implementation must bind its exact supported version later and must not grant
application roles superuser, ownership, or `BYPASSRLS` privileges.

### Supply-Chain Evidence

| Source | Relevant primary guidance | Bounded H-CAM implication |
| --- | --- | --- |
| [SLSA 1.2](https://slsa.dev/spec/v1.2/) | Defines build and source tracks, levels, provenance, and verification expectations | Store claimed track/level separately from evidence and default to `not_assessed` until every requirement is verified |
| [SLSA provenance](https://slsa.dev/spec/v1.2/provenance) | Describes verifiable information about where, when, and how an artifact was produced | Bind artifacts to source, builder, parameters, dependencies, and immutable digests |
| [SPDX 3.0.1](https://spdx.github.io/spdx-spec/) | Open BOM model for software, builds, AI, datasets, licenses, security, and provenance | Use an internal canonical bundle with a versioned SPDX projection, not ad hoc dependency text |
| [SPDX conformance](https://spdx.github.io/spdx-spec/v3.0.1/conformance/) | Defines mandatory core and optional profile compliance points | Do not claim SPDX conformance until exact import/export requirements are validated |
| [CycloneDX overview](https://cyclonedx.org/specification/overview/) | Models components, services, dependencies, formulation, vulnerabilities, and VEX | Support an optional projection for operational vulnerability workflows while preserving completeness state |

The observed current versions were SLSA 1.2, SPDX 3.0.1, and CycloneDX 1.7.
These are research observations. Future implementation must pin exact schemas,
validators, and licenses and must preserve `unknown` and `incomplete` states.

### Kubernetes And Hardware-Aware Placement

| Source | Relevant primary guidance | Bounded H-CAM implication |
| --- | --- | --- |
| [Kubernetes observability](https://kubernetes.io/docs/concepts/cluster-administration/observability/) | Metrics, logs, and traces provide different views | Map H-CAM typed signals to cluster facilities without combining their retention or authority |
| [Kubernetes logging architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/) | Kubernetes does not provide native durable log storage; cluster-level storage is external | Require an explicit sink capability and retention contract before enabling export |
| [Kubernetes probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/) | Startup, readiness, and liveness have different effects; bad liveness probes can cascade | Generate distinct probes from H-CAM health states and never use dependency outage alone as liveness failure |
| [Kubernetes disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) | Pod disruption budgets cover only some voluntary disruptions | Model PDBs as one control, not an availability guarantee |
| [Topology spread constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) | Spreads pods across declared failure domains | Require topology labels and evidence that configured domains exist |
| [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/) | Baseline and Restricted profiles constrain pod privileges | Target Restricted where compatible and record narrow exceptions; never use removed PodSecurityPolicy |
| [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/) | Enforcement depends on the network plugin and is primarily layer 4 | Require capability evidence from the selected CNI and default-deny ingress/egress design |
| [Kubernetes DRA](https://kubernetes.io/docs/concepts/resource-management/dynamic-resource-allocation/) | Stable resource claims can allocate and share accelerators; preemption has limitations | Keep accelerator requests behind a placement adapter and provide device-plugin compatibility where needed |
| [Kubernetes device plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/) | Vendor plugins advertise specialized hardware to kubelet | Consume declared allocatable resources; do not inspect or configure devices from application code |

The current Kubernetes documentation observed during research describes DRA
as stable since v1.35 and highlights version-dependent features in v1.36 and
v1.37 documentation. H-CAM must record cluster version and feature support and
must fail closed rather than assuming the newest behavior.

## Research Conclusions

1. **Preserve Prometheus; add contracts, not a forced backend.** Existing
   metrics are valuable. P4.6 should introduce a central registry, static
   cardinality checks, and optional OTel-compatible exporters behind no-op
   defaults.
2. **Separate signal authority.** Metrics are aggregate health, traces are
   diagnostic causality, operational logs describe service behavior, security
   logs support detection/response, audit records prove attributable control
   changes, and evidence records preserve investigation provenance. No signal
   silently substitutes for another.
3. **Use bounded correlation context.** W3C trace context may cross service
   boundaries. Department IDs, camera IDs, people, plates, credentials,
   reasons, free text, and evidence identifiers do not belong in metric labels
   or propagated baggage.
4. **Do not select production SLO numbers during planning.** Define schema,
   windows, indicators, exclusions, and approval states. Targets remain
   `unset` until generated and owned-environment evidence supports an owner
   decision.
5. **Keep domain workers authoritative.** A typed resilience policy and
   conformance suite should span domains, while jobs and business outcomes
   remain in domain stores. PostgreSQL claims use leases and `SKIP LOCKED` only
   for queue-like work.
6. **Layer kill switches and degradation.** Global, department, capability,
   provider, model, and worker controls must be revisioned, attributable,
   default deny, and incapable of enabling a feature whose lower gate is off.
7. **Test both authorization layers.** Passing API RBAC tests does not prove
   RLS. Passing normal-role RLS tests does not cover table owners,
   `BYPASSRLS`, superusers, policy absence, or integrity side channels.
8. **Generate interoperable supply-chain projections from one canonical
   bundle.** SPDX, CycloneDX, and SLSA answer overlapping but different
   questions. Missing evidence stays unknown; no generated file alone proves a
   level or compliance status.
9. **Restore evidence is the recovery truth.** Backup success is an input.
   Recovery claims require an isolated restore, integrity checks, service
   reconstruction, measured RPO/RTO, and a retained sanitized drill record.
10. **Make placement capability-driven.** The same requested service graph can
    compile to laptop, GPU lab, server, or Kubernetes plans. Unsupported layers
    are bypassed only through explicit typed policy, not silent fallback.
11. **C1/C10/C50 remains generated-only.** Profiles use synthetic identifiers
    and events, no cameras or media. Results bind source, configuration,
    hardware class, workload, duration, warmup, latency, throughput, backlog,
    saturation, failures, recovery, and limitations.
12. **Kubernetes is optional.** Standalone execution remains a first-class
    topology. Kubernetes manifests, policies, DRA, device plugins, probes,
    disruption budgets, and topology rules require separate implementation and
    owned-cluster validation before any readiness claim.

## Explicit Non-Claims

- No service-level target, availability level, capacity, RPO, RTO, or recovery
  objective has been achieved.
- No OpenTelemetry, SLSA, SPDX, CycloneDX, NIST, Kubernetes, or PostgreSQL
  conformance or compliance status is claimed.
- No telemetry backend, SIEM, collector, scheduler, container, cluster,
  accelerator, scanner, backup target, or restore target was contacted.
- No process, test, load, capacity, hardware, recovery, backup, restore,
  container, or Kubernetes operation was executed under this research.
- No source, media, private data, Government data, credential, model, dataset,
  or artifact was accessed or acquired.

## Research Status

Official primary-source research and repository inventory are complete for the
P4.6 planning decision. Open owner decisions and later implementation evidence
remain separate gates. Research completion earns **0 P4.6 points** and changes
Phase 4 by **+0.00 percentage points**.
