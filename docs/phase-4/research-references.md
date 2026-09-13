# Phase 4 Research References

Status: primary-source planning research checked on 2026-09-03. Versions and
guidance can change; implementation must recheck exact current sources and bind
exact dependency artifacts before use.

## Common Expression Language

- [CEL home](https://cel.dev/)
- [CEL overview](https://cel.dev/overview/cel-overview)

Current official guidance describes CEL as non-Turing complete, limited to data
provided by the host, and suited to compile-once/evaluate-many use. The overview
also separates parse, type-check, and evaluation stages and advises against
parsing/checking in latency-critical paths.

H-CAM implication: retain stateful temporal behavior in typed H-CAM nodes;
allow CEL only for stateless predicates over a closed host context; store the
checked canonical form; do not expose custom I/O or arbitrary extensions.

## Event-Time Complex Event Processing

- [Apache Flink event-time applications](https://flink.apache.org/what-is-flink/flink-applications/)
- [Apache Flink CEP documentation](https://nightlies.apache.org/flink/flink-docs-stable/docs/libs/cep/)
- [Apache Flink watermark generation](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/event-time/generating_watermarks/)

Flink's official documentation distinguishes event time from processing time
and documents watermarks, late-event handling, bounded pattern intervals, and
match skip strategies.

H-CAM implication: use these as design evidence for deterministic event-time
windows, lateness, overlap, and replay. This planning package does not select or
install Flink; the H-CAM contract must remain independent of an execution
library.

## Temporal Graph Learning

- [Temporal Graph Networks paper](https://arxiv.org/abs/2006.10637)

The primary TGN paper presents dynamic graphs as sequences of timed events and
combines memory modules with graph operators for transductive and inductive
prediction tasks.

H-CAM implication: a TGN-family model is a future candidate generator or ranker,
not an identity or alert authority. It requires exact model, dataset, license,
calibration, drift, subgroup, replay, resource, and rollback evidence before
promotion. No TGN implementation or dependency is selected now.

## Probabilistic Evidence Fusion

- [Factor Graphs and the Sum-Product Algorithm](https://doi.org/10.1109/18.910572)

The factor-graph paper represents a global function through local factors and
describes message-passing computation of exact or approximate marginal
functions.

H-CAM implication: a future generated-only factor-graph lane may expose typed
spatial, temporal, source, freshness, and contradiction contributions. Priors,
factor dependencies, approximation, conflict, and normalization must be
versioned and visible; an apparently precise result is not automatically
trustworthy.

## Calibration, Ensembles, And Abstention

- [On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a.html)
- [Simple and Scalable Predictive Uncertainty Estimation Using Deep Ensembles](https://papers.nips.cc/paper_files/paper/2017/hash/9ef2ed4b7fd2c810847ffa5fa85bce38-Abstract.html)
- [Selective Classification for Deep Neural Networks](https://papers.neurips.cc/paper_files/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html)

The calibration paper shows that neural-network confidence can be poorly
calibrated and evaluates post-hoc calibration. The ensemble paper evaluates a
parallelizable uncertainty approach, while selective classification defines a
reject option that trades coverage for lower accepted risk.

H-CAM implication: never present raw model score as probability. Learned lanes
need held-out calibration, risk-coverage, shift, and subgroup evidence plus an
explicit abstention result. Ensembles are an optional high-resource profile;
omitting them on a laptop must be reported as a missing lane rather than
simulated evidence.

## CloudEvents

- [CloudEvents project and specification releases](https://cloudevents.io/)

CloudEvents provides a standard event envelope and reports specification 1.0.2
as compatible with 1.0. H-CAM already has a versioned outbox envelope and should
not replace it merely to adopt a standard. A future gateway may provide an
explicit, tested mapping where interoperability requires it.

H-CAM implication: preserve existing event IDs, types, schema versions,
partition keys, timestamps, and payload validation. Treat any CloudEvents
mapping as an adapter with round-trip compatibility tests.

## PostgreSQL Queue Claiming

- [PostgreSQL `SELECT` and locking clauses](https://www.postgresql.org/docs/current/sql-select.html)

Official PostgreSQL documentation says `SKIP LOCKED` gives an inconsistent view
and is unsuitable for general-purpose reads, but can reduce contention for
multiple consumers of a queue-like table.

H-CAM implication: use `FOR UPDATE SKIP LOCKED` only to lease pending work from
queue tables. Domain reads, alert state, and evidence consistency still require
transactions, unique constraints, optimistic concurrency, and deterministic
ordering.

## PostgreSQL Row Security

- [PostgreSQL row-security policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

Current PostgreSQL documentation describes per-row policies as an additional
restriction beyond normal privileges. It also documents default denial when row
security is enabled without an applicable policy, while superusers, roles with
`BYPASSRLS`, and normally table owners can bypass row security.

H-CAM implication: department isolation must remain enforced in application
authorization and use forced row security as defense in depth. Product runtime
roles cannot be superusers, table owners, or have `BYPASSRLS`; direct database
isolation and maintenance-role misuse require explicit negative tests.

## PostGIS Spatial Queries

- [PostGIS spatial-index guidance](https://postgis.net/documentation/faq/spatial-indexes/)
- [PostGIS `ST_Intersects`](https://postgis.net/docs/en/ST_Intersects.html)
- [PostGIS `ST_Transform`](https://postgis.net/docs/en/ST_Transform.html)
- [PostGIS `ST_IsValid`](https://postgis.net/docs/en/ST_IsValid.html)
- [IETF RFC 7946 GeoJSON](https://www.rfc-editor.org/rfc/rfc7946)

PostGIS documents GiST spatial indexes, index-aware spatial predicates such as
`ST_Intersects`, `ST_Contains`, and `ST_DWithin`, geometry validity checks, and
explicit coordinate transformation. RFC 7946 defines GeoJSON interoperability
around WGS84 longitude/latitude coordinates.

H-CAM implication: PostGIS can support approved camera groups, administrative
areas, and explicit map relationships. APIs should accept one bounded GeoJSON
profile, while storage declares and validates SRID and transforms. Invalid or
ambiguous geometry fails closed. Spatial feasibility must not convert
image-space tracks or proximity into cross-camera identity.

## Evidence Provenance

- [W3C PROV model primer](https://www.w3.org/TR/prov-primer/)
- [W3C PROV data model](https://www.w3.org/TR/prov-dm/)
- [W3C PROV constraints](https://www.w3.org/TR/prov-constraints/)

The W3C PROV family separates entities, activities, agents, derivations,
revisions, roles, and time. It is a useful conceptual basis for reconstructing
how an output was produced and who or what was responsible.

H-CAM implication: model immutable event, rule, hypothesis, alert, timeline, and
export versions as entities; processing and review as activities; and users,
services, organizations, and versioned runtimes as attributable agents. Use a
small typed H-CAM projection and do not claim formal PROV conformance without a
separate mapping and validation milestone.

## AI Risk And Human Oversight

- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST AI RMF 1.0 publication](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10)
- [NIST AI RMF Playbook](https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook)
- [NIST human-AI interaction appendix](https://airc.nist.gov/airmf-resources/airmf/appendices/app-c-ai-risk-management-and-human-ai-interaction/)

NIST organizes voluntary AI risk work around Govern, Map, Measure, and Manage,
and emphasizes documented roles and responsibilities for human-AI oversight.
The framework is being revised, so it is a planning aid rather than a claim of
certification or legal compliance.

H-CAM implication: define the human/system authority boundary, retain
attributable review and correction, measure false-positive and human-factors
risks, and keep the owner responsible for accepting residual risk.

## Indian Legal Review Inputs

- [India Code: Digital Personal Data Protection Act, 2023](https://www.indiacode.nic.in/handle/123456789/22037)
- [MeitY: Digital Personal Data Protection Rules, 2025](https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa)
- [India Code: Bharatiya Sakshya Adhiniyam, 2023](https://www.indiacode.nic.in/handle/123456789/20063)

The official sources establish that commencement can be provision-specific and
that electronic or digital records have statutory treatment. Their application
to a police CCTV intelligence platform, including exemptions, lawful purpose,
controller roles, retention, disclosure, and electronic-record procedure,
cannot be resolved by a software architecture document.

H-CAM implication: maintain a versioned legal-and-policy applicability register
for every data class, provider, operational purpose, export, and deployment.
Record the source, provision, commencement state, policy owner, legal reviewer,
decision date, unresolved questions, and recheck date. Keep all real providers,
personal data, operational alerts, and evidentiary claims gated until authorized
official reviewers approve the exact use.

## Telemetry And Audit

- [OpenTelemetry event semantic conventions](https://opentelemetry.io/docs/specs/semconv/general/events/)
- [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/specs/semconv/)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

OpenTelemetry recommends stable event names with changing identifiers in
attributes and distinguishes point-in-time events from duration-bearing spans.
OWASP notes that application security logging is essential and that audit,
transaction, security, and operational records may serve different purposes.

H-CAM implication: use stable low-cardinality names and labels; keep actor,
camera, stream, alert, and provider-record identifiers out of metric labels;
and separate operational telemetry, security logs, immutable audit, and
investigation evidence by access and retention policy.

## Research Limitations

- This review does not establish Indian or Gujarat legal authority, police
  operating policy, evidentiary admissibility, data-controller roles, or
  provider permission.
- No official Sentinel, Government, police, private, or camera environment was
  accessed for Phase 4 planning.
- No dependency, model, dataset, container, credential, or external API was
  downloaded or executed.
- Exact library and server versions remain implementation decisions requiring
  supply-chain evidence and compatibility tests.
- The AMEC design is an H-CAM synthesis of researched techniques. It is not a
  claim that H-CAM invented CEL, CEP, factor graphs, temporal graph networks,
  calibration, deep ensembles, or selective classification.
