# P5.6 Official Research Record

Status date: 2026-09-10

Status: official primary-source research complete; implementation remains closed

## Purpose

This record translates official security, identity, accessibility,
observability, database, supply-chain, continuity, container, and Indian
government-web guidance into planning constraints for P5.6 Administration,
Security, And Operations. It is architecture guidance, not a compliance,
certification, legal, production-readiness, or deployment claim.

The accepted Phase 0 through P5.5 contracts remain authoritative. Where an
external source permits a broader design than an accepted H-CAM boundary, the
narrower H-CAM boundary wins.

## Research Method

- official primary technical, standards, and government sources only;
- no third-party product comparison or marketing material;
- no software installation, download, package resolution, scanner, runtime,
  browser, container, Kubernetes, provider, camera, media, or data access;
- repository analysis was read-only;
- conclusions are requirements inputs, not assertions of conformance.

## Source Register And H-CAM Consequences

| Source | Primary conclusion | P5.6 consequence |
| --- | --- | --- |
| [NIST SP 800-207, Zero Trust Architecture](https://csrc.nist.gov/pubs/sp/800/207/final) | Protect resources through explicit, continuously evaluated policy rather than trusting network location. | Every Admin, Security, and Operations request remains server-authorized; portal, workstation, subnet, or resource profile never grants authority. |
| [NIST SP 800-207A](https://csrc.nist.gov/pubs/sp/800/207/a/final) | Cloud-native access control must account for user, application, and service identity across hybrid environments. | UI contracts carry authoritative subject, department, purpose, resource, and service context without making policy decisions in the browser. |
| [NIST RBAC project and FAQ](https://csrc.nist.gov/Projects/Role-Based-Access-Control) | RBAC supports role hierarchy, sessions, and static or dynamic separation of duty. | RBAC is the entitlement baseline; constrained attributes refine access. Consequential changes require typed approval and separation-of-duty policy. |
| [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) | Access control, audit, configuration, contingency, identity, incident response, privacy, and supply chain are distinct control families. | P5.6 keeps administrative change, security events, audit records, operational signals, compliance evidence, and recovery state distinct and cross-referenced. |
| [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html) | Protected channels, session limits, reauthentication, replay resistance, and phishing-resistant authentication matter for higher-risk actions. | Step-up and reauthentication are planned as server-produced requirements. P5.6 does not fake or locally satisfy them. Privileged action stays unavailable without a trusted producer. |
| [OAuth 2.0 Security BCP, RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html) | Authorization-code flows, PKCE, exact redirect matching, CSRF defenses, secure metadata, sender constraints, and TLS reduce OAuth threats. | Browser session planning preserves same-origin APIs, exact redirect policy, no token-in-URL behavior, authoritative issuer metadata, and bounded session teardown. |
| [PostgreSQL row security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) | Enabled row security without an applicable policy is default deny, while table owners normally bypass unless explicitly constrained. | Department isolation requires API authorization plus PostgreSQL RLS equivalence, forced where appropriate, tested with non-owner application roles. Client filtering is never a security boundary. |
| [OpenTelemetry specification](https://opentelemetry.io/docs/specs/otel/) | Traces, metrics, and logs share context and resource models but remain distinct signals. | P5.6 can correlate bounded signal references while preserving operational, security, audit, and evidence authority lanes. Adapters stay default-off. |
| [OpenTelemetry log data model](https://opentelemetry.io/docs/specs/otel/logs/data-model/) | Structured logs support observed time, event time, severity, trace/span context, resource, and attributes. | H-CAM projections distinguish record time, observed time, severity, trace reference, source, freshness, and sanitization without retaining arbitrary raw bodies. |
| [NIST SP 800-92](https://csrc.nist.gov/pubs/sp/800/92/final) | Enterprise log management needs deliberate infrastructure, process, retention, and review. | P5.6 presents lane-specific inventory, health, freshness, integrity, and query limits; it does not treat one combined UI search as an authoritative log store. |
| [CERT-In Directions under section 70B](https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf) and [official FAQ](https://www.cert-in.org.in/PDF/FAQs_on_CyberSecurityDirections_May2022.pdf) | The directions address clock synchronization, incident reporting, and secure ICT-log retention. | P5.6 records jurisdiction and policy references, clock health, retention source, and unknown status. It does not choose legal applicability, retention periods, or reporting procedures. |
| [NIST SP 800-34 Rev. 1](https://csrc.nist.gov/pubs/sp/800/34/r1/upd1/final) | Contingency planning includes impact analysis, recovery strategies, plans, testing, training, and maintenance. | Backup, restore, disaster-recovery, RPO, and RTO surfaces show declared targets, evidence age, drill history, dependencies, and limitations; no recovery action or target is activated in P5.6. |
| [Kubernetes RBAC good practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/) | Least privilege, namespaced scope, avoidance of wildcards and superuser use, and periodic review reduce privilege escalation. | Kubernetes remains a future deployment projection. UI views identify wildcard, cluster-wide, service-account, and privilege-escalation risks but cannot mutate a cluster. |
| [Kubernetes auditing](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/) | Kubernetes audit records answer who, what, when, where, and outcome questions at defined request stages. | Future Kubernetes projections preserve actor, resource, verb, stage, outcome, source, and policy identity as typed references; no audit backend is activated. |
| [Kubernetes Secrets good practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/) | Secret access needs encryption, least privilege, restricted listing, auditing, and protection after use. | The browser receives opaque secret references and provider health metadata only. Secret values, reveal, validation, rotation, and resolution are absent. |
| [SLSA specification](https://slsa.dev/spec/v1.2/) and [SLSA provenance](https://slsa.dev/spec/v1.2/provenance) | Verifiable provenance relates artifacts to source and build processes through structured attestations. | Supply-chain views separate asserted provenance, verified provenance, policy assessment, freshness, subject identity, and missing evidence. No SLSA level is claimed. |
| [CycloneDX specification](https://cyclonedx.org/specification/overview/) | A BOM can represent components, services, dependencies, compositions, vulnerabilities, licenses, and attestations. | Existing SBOM projections remain read-only, versioned, and completeness-qualified. P5.6 will not generate or refresh a production SBOM or scanner result. |
| [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) | ASVS provides testable requirements for web application security controls. | The P5.6 implementation plan includes threat-to-test traceability for authentication projection, session handling, access control, validation, safe errors, and audit behavior without claiming ASVS conformance. |
| [OpenFeature specification](https://openfeature.dev/specification/) | Feature evaluation has typed values, provider behavior, evaluation context, hooks, events, and safe defaults. | Feature controls use typed revisions, server-authoritative evaluation, explicit reason and variant, sanitized context, stale/provider states, and deny-safe defaults. No frontend flag SDK is required initially. |
| [OPA authorization documentation](https://www.openpolicyagent.org/docs/http-api-authorization) | Policy engines can make fine-grained context-aware API authorization decisions. | A future backend policy adapter is possible, but P5.6 does not add OPA, policy bundles, a network sidecar, or browser policy execution. |
| [WCAG 2.2](https://www.w3.org/TR/WCAG22/) | Accessible content requires perceivable, operable, understandable, and robust behavior, including visible focus and accessible authentication. | Native tables, forms, dialogs, focus management, keyboard paths, status announcements, non-color state, target size, and reauthentication handoff are required. |
| [GIGW 3.0 accessibility guidance](https://guidelines.india.gov.in/accessibility-guidelines-and-attributes/) | Indian government sites and apps should provide text alternatives and WCAG-derived accessibility. | Every chart, topology, relationship, and status visualization has a complete authoritative table or list alternative. |
| [GIGW 3.0 security guidance](https://guidelines.india.gov.in/security-guidelines-and-attributes/) | Government web resources require security throughout design, development, testing, and deployment, with RBAC, least privilege, MFA, encrypted integrations, and security audit. | P5.6 planning includes secure-by-design evidence, least privilege, typed provider boundaries, dependency posture, and a production audit prerequisite, but does not claim safe-to-host certification. |
| [Digital Personal Data Protection Act, 2023](https://www.meity.gov.in/writereaddata/files/Digital%20Personal%20Data%20Protection%20Act%202023.pdf) | Digital personal data processing must balance lawful purposes with protection of individuals. | P5.6 minimizes administrative and security projections, uses opaque identifiers where possible, prohibits real personal data, and leaves applicability, lawful basis, notice, retention, and policy decisions to authorized governance. |

## Reconciled Design Principles

1. **Server authority:** the UI renders permissions, capabilities, decisions,
   and outcomes returned by authoritative producers; it never grants itself a
   capability.
2. **Default deny:** absent policy, stale policy, unknown department, missing
   purpose, failed reauthentication, unresolved conflict, or unavailable
   enforcement producer results in an unavailable action.
3. **Two-level isolation:** application authorization and PostgreSQL RLS must
   agree on department and resource scope. Both require independent tests.
4. **Typed change control:** no arbitrary JSON editor. Configuration changes
   use bounded schemas, revisions, validation, impact preview, approval,
   scheduled effect, supersession, and rollback references.
5. **Separation of duty:** proposer, approver, and executor eligibility are
   policy decisions, not labels. Self-approval stays denied when policy
   requires independent approval.
6. **No secret material in the browser:** secret references, provider type,
   health state, revision, last rotation observation, and policy status may be
   visible. Values and credential operations may not.
7. **Signal separation:** operational telemetry, security events, immutable
   audit, and evidence records retain separate schemas, access rules,
   retention authorities, and source-of-truth links.
8. **Truth-qualified status:** `healthy`, `compliant`, `verified`, `current`,
   `protected`, and `ready` always carry producer, observation time,
   completeness, freshness, policy version, and limitations.
9. **Hardware-neutral authority:** resource profiles change rendering density,
   refresh cadence, query page size, and optional visual layers only. They do
   not change authorization, data scope, truth, or action eligibility.
10. **Non-operative previews:** deployment, retention, recovery, kill-switch,
    provider, model-lane, and policy controls remain generated projections
    until separately authorized producers and enforcement paths exist.

## Explicit Non-Claims

P5.6 planning does not claim:

- NIST, OWASP, WCAG, GIGW, CERT-In, SLSA, CycloneDX, Kubernetes, OAuth, or
  OpenTelemetry conformance;
- production security, availability, capacity, RPO, RTO, or SLO readiness;
- legal applicability, compliance, admissibility, retention, or reporting
  conclusions;
- identity-provider, SIEM, secret-store, policy-engine, scanner, telemetry,
  backup, cluster, or infrastructure integration;
- a real administrative mutation or operational control path.

## Research Outcome

The official sources support a connected three-portal P5.6 architecture:

- **Admin Center** for typed governance proposals, approvals, configuration
  history, and non-effective resource/provider/profile projections;
- **Security Center** for access posture, denied activity, audit references,
  policy exceptions, supply-chain evidence, session/authentication health, and
  compliance evidence workflows;
- **Operations Center** for camera operations already accepted in P5.3 plus a
  separate platform-health domain covering services, queues, workers, storage,
  databases, event bus, media edge, AI runtime, SLOs, degradation, recovery,
  maintenance, and capacity projections.

The research adds no product points. P5.6 remains 0/10 and Phase 5 remains
78/100 until bounded implementation and exact acceptance occur.
