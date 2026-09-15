# P4.5 Investigation Timeline And Evidence Research Record

Status date: 2026-09-05

Status: official primary-source research complete for planning. This document
is non-effective and does not make a legal, records-retention, evidentiary,
hold, deletion, or export decision.

## Authority And Method

Research was performed under `D-P4.5-PLAN-AUTH`. Only official standards-body,
Government, security, privacy, records-management, and digital-evidence sources
were used. No provider, Sentinel, camera, media, investigation, Government,
private, credential, model, dataset, or deployment access occurred.

The sources guide architecture and test design. They do not establish that
H-CAM output is admissible evidence, determine which law applies to a Gujarat
deployment, set a retention period, authorize a hold or deletion, or claim
conformance to any cited standard.

## Repository Baseline

P4.0 already created a deliberately narrow generated-only foundation:

- `TimelineEntryV1` supports source facts, system hypotheses, operator
  observations, review decisions, and corrections;
- `InvestigationTimeline` supports only `draft` and `closed` states;
- `timeline_entries` stores a source reference/digest, sequence, actor, reason,
  occurred/recorded timestamps, payload digest, and retention class;
- timeline reads are department-scoped and runtime-disabled;
- the database enforces generated-only rows and PostgreSQL row security.

P4.5 therefore extends rather than replaces that foundation. The current V1
contracts remain readable. P4.5 planning adds versioned contracts, complete
chronology, immutable evidence-reference states, provenance and derivation,
correction propagation, non-destructive merge/reopen workflows, policy-bound
retention and hold overlays, deletion execution evidence, and reference-only
exports.

## Official Primary Sources

### Provenance And Derivation

1. W3C, PROV-DM: The PROV Data Model:
   <https://www.w3.org/2012/10/prov-dm>

   PROV separates entities, activities, and agents, and relates use,
   generation, derivation, attribution, association, revision, quotation, and
   primary sources. H-CAM should use these concepts for immutable versions and
   attributable transformations without claiming PROV conformance.

2. W3C, Constraints of the PROV Data Model:
   <https://www.w3.org/TR/prov-constraints/>

   Provenance validity requires uniqueness, ordering, typing, and impossibility
   constraints. H-CAM needs structural graph validation, causal-order checks,
   and fail-closed handling of inconsistent provenance.

3. W3C, PROV-AQ: Provenance Access and Query:
   <https://www.w3.org/TR/prov-aq/>

   Provenance retrieval can be separate from the resource itself. This supports
   purpose-bound evidence/provenance APIs and reference-only source handling.

### Digital Evidence Preservation

4. NIST IR 8387, Digital Evidence Preservation: Considerations for Evidence
   Handlers:
   <https://www.nist.gov/publications/digital-evidence-preservation-considerations-evidence-handlers>

   Digital evidence has preservation problems beyond traditional evidence and
   includes law-enforcement-generated digital evidence. H-CAM must distinguish
   source preservation from derived intelligence, preserve integrity metadata,
   and make unavailable or unverifiable states explicit.

5. NIST SP 800-86, Guide to Integrating Forensic Techniques into Incident
   Response:
   <https://csrc.nist.gov/pubs/sp/800/86/final>

   This is technical guidance, not legal advice or a complete law-enforcement
   procedure. It supports documented collection/analysis processes, source
   identification, integrity checks, and reproducibility while leaving legal
   procedure to authorized policy owners.

6. ISO/IEC 27037:2012 official abstract:
   <https://www.iso.org/standard/44381.html>

   The standard covers identification, collection, acquisition, and
   preservation of potential digital evidence, including CCTV. H-CAM uses the
   concepts as design input only and does not claim certification or conformity.

### Integrity, Canonicalization, And Long-Term Verification

7. NIST FIPS 180-4, Secure Hash Standard:
   <https://csrc.nist.gov/pubs/fips/180-4/upd1/final>

   Secure message digests can detect change. H-CAM must record algorithm and
   version with every digest and plan algorithm agility; a hash alone does not
   prove origin, custody, completeness, authenticity, or legal admissibility.

8. RFC 8785, JSON Canonicalization Scheme:
   <https://www.rfc-editor.org/rfc/rfc8785.html>

   Cryptographic operations require invariant representation. Canonical JSON
   must reject duplicate names and invalid values, preserve strings, and sort
   properties deterministically. H-CAM should bind manifest and projection
   digests to a named canonicalization profile.

9. RFC 3161, Time-Stamp Protocol:
   <https://www.rfc-editor.org/info/rfc3161/>

   A trusted timestamp can bind a message imprint to a time. H-CAM should define
   a future optional timestamp-receipt slot, but no timestamp authority,
   certificate, network call, or validity claim is authorized in P4.5.

10. RFC 4998, Evidence Record Syntax:
    <https://www.rfc-editor.org/info/rfc4998/>

    Evidence records can preserve verification material over long periods and
    support hash-tree and timestamp renewal. H-CAM should keep algorithm,
    verification, and renewal metadata extensible without implementing ERS or
    claiming long-term non-repudiation in the generated baseline.

11. RFC 8493, BagIt File Packaging Format v1.0:
    <https://www.rfc-editor.org/info/rfc8493/>

    BagIt defines file-content and metadata manifests for storage/transfer.
    H-CAM should use a native reference-only canonical export manifest first and
    reserve optional BagIt payload packaging for a separately authorized export
    profile that may copy content.

### India Legal And Records Context

12. India Code, Bharatiya Sakshya Adhiniyam, 2023:
    <https://www.indiacode.nic.in/handle/123456789/20063?locale=en>

    Sections 61 through 63 address electronic or digital records and their
    admissibility. Architecture must preserve the inputs and metadata needed for
    authorized personnel to assess applicable requirements; H-CAM must not label
    an item legally admissible or generate legal certification autonomously.

13. MeitY, Digital Personal Data Protection Act, 2023:
    <https://www.meity.gov.in/writereaddata/files/Digital%20Personal%20Data%20Protection%20Act%202023.pdf>

    The Act concerns lawful processing of digital personal data and protection
    of individuals. P4.5 should minimize copied data, bind access/export to a
    declared purpose, record accountable processing, and leave applicability,
    lawful basis, exemptions, and policy interpretation to authorized owners.

14. MeitY, Digital Personal Data Protection Rules, 2025 and official
    commencement material:
    <https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa?pageTitle=Digital-Personal-Data-Protection-Rules-2025>

    The official publication uses staged commencement. Deployment reviews must
    bind the then-effective provisions instead of treating every rule as already
    effective or hard-coding current legal interpretation into software.

15. India Code, Public Records Act, 1993:
    <https://www.indiacode.nic.in/handle/123456789/1921?locale=en>

16. National Archives of India, Public Records Rules, 1997:
    <https://nationalarchives.nic.in/en/public-record-rules-1997>

17. National Archives of India, Records Retention Schedule guidance:
    <https://www.nationalarchives.nic.in/en/record-management/records-retention-schedule-rrs>

    These sources illustrate accountable records officers, retention schedules,
    periodic review, recorded destruction, and retained destruction lists. Their
    legal scope is not assumed to cover H-CAM or a Gujarat Police deployment.
    They support a policy-reference architecture, not a selected schedule.

18. CERT-In directions under section 70B:
    <https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf>

    Security-log obligations must be analyzed separately from investigation
    evidence. H-CAM must not merge security, audit, operational, investigation,
    or source-media retention merely because they share timestamps or IDs.

### Security, Privacy, And Audit Controls

19. NIST SP 800-53 Rev. 5, Security and Privacy Controls:
    <https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final>

    The access-control, audit/accountability, media-protection, privacy, and
    system-integrity control families support least privilege, attributable
    operations, controlled media handling, and integrity monitoring. H-CAM maps
    relevant outcomes but does not claim a NIST control baseline.

20. NIST Privacy Framework:
    <https://www.nist.gov/privacy-framework>

    Data processing should be governed across its lifecycle. Purpose, data
    class, minimization, retention, access, correction, and deletion state need
    explicit policy references and observable outcomes.

## Research Conclusions

### Evidence Is Not A Timeline Entry

A timeline entry is a chronological assertion or recorded action. Evidence is
an immutable, integrity-addressed reference to a source or derived entity. One
evidence entity may appear in many timelines, and one entry may cite many
evidence entities in different roles. Neither should own or silently copy the
source media.

### Integrity Has Several Independent States

`sha256:<digest>` is not a complete integrity statement. P4.5 needs separate:

- reference resolution state: resolvable, unavailable, denied, or unknown;
- verification state: not assessed, verified, mismatch, or unverifiable;
- preservation state: source-managed, H-CAM-managed-derived-only, expired,
  deletion pending, deletion recorded, or residual copies reported;
- provenance completeness: complete, partial, inconsistent, or unknown;
- algorithm/version and verification timestamp;
- verifier activity and policy identity.

No state may be collapsed into `valid evidence` or `admissible evidence`.

### Chronology Requires Multiple Clocks

P4.5 must not sort only by event time. It needs source occurrence time, source
observation time where supplied, H-CAM receipt time, durable record time,
effective correction time, and aggregate sequence. Unknown or untrusted source
time is a typed state. Causal constraints are enforced only where known; clock
skew must not force false chronology.

### Corrections Never Rewrite History

A correction or retraction creates a new immutable entity and relationship to
the affected assertion. Downstream hypotheses, alerts, timeline projections,
indexes, and export manifests receive new revisions or impact records. Earlier
bytes, reviews, and actions remain attributable and reconstructable.

### Holds Overlay Retention

Retention class selects a policy reference, not a hard-coded period. A hold is
a separately authorized, attributable, scoped overlay with lifecycle and
reason. It can prevent eligible deletion but cannot silently broaden access,
change evidence meaning, or rewrite retention policy. Conflicts stop closed.

### Deletion Evidence Is Not Absolute Proof

The system can record an authorized deletion request, evaluated policy, targets,
method class, executor, outcome, verification, exceptions, and known residual
locations. It cannot prove that every unknown copy, backup, cache, export, or
external source ceased to exist. Wording must use `deletion execution evidence`
or `deletion receipt`, never an unconditional `proof of deletion` claim.

### Export Is A New Derived Entity

Every export manifest is purpose-bound, scoped, versioned, canonicalized,
integrity-addressed, attributable, and linked to exact source versions. Default
exports contain references and minimized metadata only. Copying media or source
documents is a distinct export profile requiring explicit authorization and
policy validation.

## Unresolved Policy And Legal Questions

P4.5 implementation cannot resolve these questions:

- which statutes, rules, court procedures, police standing orders, archives
  policies, and departmental policies apply to each deployment;
- who may designate a record as evidence, authorize a hold, release a hold,
  approve deletion, certify an export, or attest to a process;
- exact retention periods, review intervals, backup treatment, jurisdiction,
  security classification, and archival transfer rules;
- whether a given electronic record or process satisfies admissibility,
  certification, chain-of-custody, or evidentiary requirements;
- approved digest, signature, trusted-time, key-management, and long-term
  validation profiles for a production deployment.

These remain explicit policy bindings and deployment gates.

## Planning Invariants Derived From Research

1. Original source bytes are outside the default P4.5 store.
2. Evidence identity and interpretation are separate.
3. Every material version and transition is append-only and attributable.
4. Every derived entity links to exact input versions and producing activity.
5. Graphs reject cycles, duplicate identities, cross-department edges, and
   unbounded traversal.
6. Unknown, partial, conflicting, stale, unavailable, and unverifiable states
   remain visible.
7. A correction cannot erase prior knowledge, review, or action.
8. Merge uses aliases and relationships; it never deletes a timeline.
9. Reopen creates a new aggregate revision and reason.
10. Retention periods are policy data, not application constants.
11. Holds and access permissions are independent.
12. Deletion is a workflow with evidence and residual-state reporting.
13. Export is a derived entity with exact purpose and source closure.
14. Audit, security logs, operational telemetry, investigation records, and
    evidence references remain separate data classes.
15. Generated validation uses non-issuable identifiers and no real content.

## Source Review Triggers

Research must be refreshed before a real-data, real-investigation, retention,
hold, deletion, signature/timestamp, export, or deployment authorization. It
must also be refreshed when cited law/rules commence or change, NIST revises a
cited publication, an integrity algorithm profile changes, or the organization
adopts a records/evidence policy.
