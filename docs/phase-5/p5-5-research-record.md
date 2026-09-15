# P5.5 Official Primary-Source Research Record

Status date: 2026-09-09

Status: planning research complete; owner decisions and implementation remain pending

## Method

Research was limited to official standards bodies, national technical
authorities, and primary legislation repositories. No operational system,
provider, camera, media source, investigation, evidence object, credential,
model, dataset, or private or Government data was accessed. Legal sources are
recorded as design constraints, not legal advice or a product determination of
admissibility, retention, custody, or lawful purpose.

## Provenance And Derivation

### W3C PROV-DM

The [W3C PROV Data Model](https://www.w3.org/TR/prov-dm/) defines provenance
around entities, activities, agents, derivations, responsibility, bundles, and
collections. P5.5 should therefore preserve typed nodes and edges rather than
flattening lineage into a narrative string.

Planning consequences:

- keep H-CAM evidence references, generated derivations, operator activities,
  and attributable agents visually and semantically distinct;
- let one entity have multiple derivations and responsibility links;
- represent provenance-of-provenance through immutable bundle versions;
- treat a PROV projection as an interchange view, not the authoritative H-CAM
  record or an authorization grant;
- preserve the Phase 4.5 prohibition on external PROV import.

### W3C PROV Constraints

The [W3C PROV Constraints](https://www.w3.org/TR/prov-constraints/) describe
uniqueness, event ordering, type, and impossible-pattern constraints. Their use
of "valid" means consistency with the PROV model, not factual truth or legal
validity.

Planning consequences:

- show graph consistency separately from source integrity and legal state;
- preserve deterministic ordering and typed edge constraints;
- expose incomplete, inconsistent, cyclic, or unavailable projections as
  explicit states;
- never label a graph `true`, `authentic`, `admissible`, or `proven` merely
  because structural validation passes.

## Digital Evidence Preservation

### NISTIR 8387

[NISTIR 8387, Digital Evidence Preservation: Considerations for Evidence
Handlers](https://www.nist.gov/publications/digital-evidence-preservation-considerations-evidence-handlers)
addresses the distinct preservation requirements of digital evidence and the
relationship between evidence management, digital objects, storage media, and
law-enforcement-generated material.

Planning consequences:

- identify the referenced source and its observed version without resolving or
  copying it in P5.5;
- present availability, integrity observation, provenance, custody history,
  and legal assessment as separate dimensions;
- preserve every verification observation instead of replacing the prior one;
- record inability to verify as `unavailable` or `unknown`, never as success;
- keep external custody and physical handling outside H-CAM's asserted
  knowledge.

### NIST Evidence Management

The [NIST Evidence Management](https://www.nist.gov/forensic-science/interdisciplinary-topics/evidence-management)
material emphasizes avoiding compromise, contamination, and degradation while
tracking custody. H-CAM can display supplied custody events and system access
history, but it cannot infer an uninterrupted physical or external-system
chain.

Planning consequences:

- use append-only custody-event projections with source and authority labels;
- show gaps, unknown intervals, and source-system boundaries;
- never convert an H-CAM access log into a custody event automatically;
- distinguish collection, registration, verification, access, transfer,
  derivation, correction, and disposition events.

## Indian Electronic-Record Constraints

### Bharatiya Sakshya Adhiniyam, 2023

The official [India Code record](https://www.indiacode.nic.in/handle/123456789/20063)
and [Act text](https://www.indiacode.nic.in/indiacode/bitstream/123456789/20063/1/aa202347.pdf)
include electronic and digital records within documents and establish specific
conditions and certificate information for electronic-record admissibility.

Planning consequences:

- preserve source-system, device/process, production-method, time, actor, and
  version references when producers make them available;
- provide neutral fields for separately authorized certification metadata;
- do not generate, sign, claim, or simulate a legal certificate in P5.5;
- do not equate a digest match, H-CAM reconstruction, or provenance graph with
  satisfaction of statutory conditions;
- require deployment-specific legal review before any admissibility wording or
  procedure is enabled.

### Information Technology Act, 2000

The official [India Code Information Technology Act record](https://www.indiacode.nic.in/handle/123456789/13683)
includes electronic-record retention, audit, attribution, acknowledgment, and
secure electronic-record provisions.

Planning consequences:

- preserve originator and system-attribution fields as supplied assertions;
- keep audit records separate from evidence records and investigation entries;
- expose the named security/canonicalization profile for integrity metadata;
- make policy and legal authority external references, never client defaults.

### Digital Personal Data Protection Act, 2023

The [India Code DPDP Act record](https://www.indiacode.nic.in/indiacode/handle/123456789/22037)
states the purpose of protecting digital personal data while allowing lawful
processing. Its provisions have a phased commencement schedule, so current
applicability must be verified by qualified deployment owners.

Planning consequences:

- minimize identifiers and source locator exposure by default;
- require department, purpose, role, and current capability for every read;
- keep sensitive details out of URLs, telemetry, browser storage, exports, and
  cross-portal navigation state;
- make retention and deletion behavior policy supplied and deployment bound;
- do not encode a claim about lawful basis or current legal applicability.

### CERT-In Directions

The official [CERT-In Directions under section 70B](https://www.cert-in.org.in/Directions70B.jsp)
and [directions PDF](https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf)
require covered organizations to enable and securely retain ICT-system logs
for the specified period. This is a cybersecurity-log requirement and does not
make those logs investigation evidence automatically.

Planning consequences:

- keep security logs, audit records, timeline entries, custody events, and
  evidence references as distinct record classes;
- do not copy security-log bodies into evidence views;
- show the source record class and policy reference when a timeline links to a
  log reference;
- leave actual period, jurisdiction, and applicability decisions outside P5.5.

## Records Lifecycle

The US National Archives [agency recordkeeping requirements](https://www.archives.gov/records-mgmt/policy/agency-recordkeeping-requirements.html)
and [disposition instructions](https://www.archives.gov/records-mgmt/scheduling/instructions)
are informative records-management examples, not legal authority for Gujarat
Police. They demonstrate why systems need documented retrieval across a record
lifecycle and explicit disposition instructions instead of ad hoc deletion.

Planning consequences:

- display policy reference, version, evaluator, effective interval, and result;
- separate retention evaluation, hold overlay, deletion intent, per-target
  outcome, and residual state;
- prohibit wildcard holds and universal-deletion claims;
- keep all P5.5 hold, deletion, and export controls preview-only.

## HTTP Authority And Integrity Manifests

### RFC 9110

[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) defines strong entity
tag comparison for `If-Match` and its use in preventing lost updates.

Planning consequences:

- bind every mutation draft to the displayed aggregate revision and strong
  ETag;
- require an idempotency identity in addition to `If-Match`;
- on conflict, retain the user's draft in memory, fetch current authority, and
  require explicit reconsideration;
- never let an event payload silently overwrite authoritative HTTP state.

### RFC 9457

[RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) defines problem details
for HTTP APIs. P5.5 should route behavior by stable type/status/extension fields
and use human-readable detail only as display text.

### RFC 8785

[RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html) defines a JSON
Canonicalization Scheme for repeatable hashing. It is an Informational RFC, not
an Internet Standards Track specification.

Planning consequences:

- evidence and export manifests must name their canonicalization profile;
- hashes bind exact canonical bytes, not a visually similar object;
- malformed Unicode, duplicate keys, unsupported numeric forms, and profile
  mismatch fail closed;
- initial P5.5 may consume Phase 4.5 canonical digests without adding a browser
  cryptography or canonicalization dependency.

## Accessibility And Large Chronologies

### WCAG 2.2

The [W3C WCAG 2.2 Recommendation](https://www.w3.org/TR/WCAG22/) requires,
among other criteria, meaningful sequence, logical focus order, visible and
unobscured focus, non-color-only information, status messages, and error
prevention for consequential submissions.

Planning consequences:

- the authoritative timeline is a semantic list or table with bounded pages;
- every visual lane, graph, diff, and status has a complete text/table
  equivalent in the same application;
- preview and mutation confirmation cannot rely on color or icon alone;
- focus returns to a stable entry after pagination, filtering, correction, or
  conflict refresh;
- destructive-looking previews need explicit non-operative labels and no
  active execution command.

### WAI-ARIA Grid Pattern

The [WAI-ARIA Authoring Practices grid pattern](https://www.w3.org/WAI/ARIA/apg/patterns/grid/)
requires application-managed focus and complete keyboard behavior when a true
interactive grid is used. A native table is simpler when cell-level editing is
not required.

Planning consequences:

- default to native table/list semantics and ordinary links/buttons;
- use a grid only for an interaction that genuinely needs cell navigation;
- do not virtualize away the focused row or silently change reading order;
- make server pagination the resource bound; optional rendering windowing is a
  subordinate enhancement.

## Access Control And Audit

[NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
separates access control, least privilege, audit generation, audit review, and
protection of audit information.

Planning consequences:

- authorize each resource and action by department, role, purpose, and current
  server capability;
- do not grant evidence access because a timeline contains a reference;
- keep audit review permissions separate from evidence and investigation
  permissions;
- attribute previews, denied operations, conflict recovery, and changes without
  logging sensitive content.

## Research Conclusions

1. P5.5 should be a connected **Investigation Center** with an integrated but
   separately authorized **Evidence Desk**; Command Center remains primary.
2. Record sequence is the authoritative append order. Event time is an asserted
   analytical view with source, precision, and trust metadata.
3. Reconstruction must bind an exact timeline revision, manifest digest,
   ordering mode, included entries, later corrections, and limitations.
4. Evidence identity, availability, integrity observation, provenance, custody,
   access authority, and legal assessment must never collapse into one badge.
5. Provenance uses the accepted Phase 4.5 typed graph, with a generated lossy
   W3C PROV projection and no external import or conformance claim.
6. Source references remain opaque. P5.5 does not resolve, render, download,
   copy, print, delete, hold, release, export, or modify source material.
7. Retention, hold, deletion, disposition, and export remain generated-only,
   non-operative previews driven by external policy references.
8. Existing frontend dependencies are sufficient for the initial plan. Server
   pagination, native semantics, and bounded internal graph adapters avoid a
   mandatory new dependency.
9. Legal applicability, admissibility, retention periods, certificates,
   physical custody, and production procedures remain deployment decisions.
