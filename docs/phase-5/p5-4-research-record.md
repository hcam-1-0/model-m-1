# P5.4 Official Primary-Source Research Record

Status: research complete for planning; informational unless an H-CAM contract says otherwise

## Method

Research was limited to official standards bodies, government technical
publications, and official dependency documentation. Sources were used to
shape accessibility, concurrency, error, event, human-review, explainability,
privacy, GIS, and dependency decisions. They do not establish legal approval,
ONVIF conformance, operational readiness, or fitness for policing.

## Accessibility And Interaction

### W3C WCAG 2.2

Source: <https://www.w3.org/TR/WCAG22/>

Planning use: preserve keyboard access, visible focus, meaningful order,
reflow, contrast, target size, reduced motion, error identification, and status
communication. Graphs and maps remain enhancements because a complete list or
table must support the same task.

### W3C Status Messages

Source: <https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html>

Planning use: routine queue refresh, save, correction, and recovery updates use
bounded polite live regions without moving focus. Assertive messages are
reserved for time-sensitive authority or draft-loss conditions.

### WAI-ARIA Authoring Practices

Sources:

- <https://www.w3.org/WAI/ARIA/apg/patterns/>
- <https://www.w3.org/WAI/ARIA/apg/patterns/grid/>
- <https://www.w3.org/WAI/ARIA/apg/patterns/treegrid/>
- <https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/>

Planning use: native tables and controls are preferred. Composite graph or
treegrid keyboard behavior must be deliberate, localized, and tested. The APG
is implementation guidance; it does not replace conformance testing.

### W3C Use Of Color And Non-Text Contrast

Sources:

- <https://www.w3.org/WAI/WCAG22/Understanding/use-of-color>
- <https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html>

Planning use: evidence role, contradiction, lifecycle, correction, focus, and
selection use text/icon/shape as well as color. Graph and map boundaries,
controls, and focus indicators require non-text contrast validation.

## HTTP Concurrency, Errors, And Idempotency

### RFC 9110 HTTP Semantics

Source: <https://www.rfc-editor.org/rfc/rfc9110.html>

Planning use: strong ETags and `If-Match` protect consequential review and
lifecycle mutations from lost updates. A failed precondition stops automatic
submission and begins an explicit refetch and reconsideration workflow.

### RFC 9457 Problem Details For HTTP APIs

Source: <https://www.rfc-editor.org/rfc/rfc9457.html>

Planning use: typed machine-readable problem responses can carry safe reason,
status, correlation, and remediation fields. Problem details must not expose
implementation internals, protected data, or security-sensitive material.

### IETF Idempotency-Key Draft

Source: <https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/>

Planning use: the draft is informative input for key uniqueness and payload
fingerprint behavior. The reviewed draft is expired and archived, not an RFC;
H-CAM therefore keeps its own typed and versioned command/idempotency contract
instead of claiming standards conformance.

## Event Contracts

### CloudEvents 1.0.2

Source: <https://cloudevents.io/>

Planning use: common event context supports typed versioning, source, subject,
time, correlation, and tracing. H-CAM events remain invalidation hints only;
authoritative state and authorization come from HTTP.

## AI Risk, Explainability, And Human Review

### NIST AI Risk Management Framework 1.0

Sources:

- <https://airc.nist.gov/airmf-resources/airmf/>
- <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf>

Planning use: validity, reliability, safety, security, accountability,
transparency, explainability, privacy, and managed bias are treated as separate
properties. A single confidence score cannot stand in for those properties.

### NIST Four Principles Of Explainable AI

Source: <https://www.nist.gov/publications/four-principles-explainable-artificial-intelligence>

Planning use: explanation views provide evidence or reasons, make information
meaningful to the reviewer, reflect the actual process, and expose knowledge
limits through uncertainty and abstention. P5.4 uses exact rule traces rather
than generated prose as authority.

### NIST AI Bias Guidance

Source: <https://www.nist.gov/artificial-intelligence/ai-fundamental-research-managing-ai-bias>

Planning use: candidate and alert views expose uncertainty, contradiction,
source, calibration class, and correction instead of hiding socio-technical
risk behind a model score. This planning does not claim bias measurement or
mitigation is complete.

### NIST Human Factors In Forensic Science

Sources:

- <https://www.nist.gov/forensic-science/human-factors-forensic-science>
- <https://nvlpubs.nist.gov/nistpubs/ir/2024/NIST.IR.8503.pdf>

Planning use: review design treats interpretation, workload, context, and
human error as system risks. The DNA-specific publication provides contextual
human-factors lessons only and is not treated as an H-CAM legal or domain rule.

### ICO Guidance On Meaningful Human Intervention

Source: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/how-do-we-ensure-individual-rights-in-our-ai-systems/>

Planning use: meaningful review requires an authorized person who can examine
relevant inputs, challenge output, and change the result. It must not be a
token approval step. This regulator guidance is informative and is not a claim
of H-CAM legal compliance in India.

## Access Control, Audit, And Privacy

### NIST SP 800-53 Rev. 5 And SP 800-53A Rev. 5

Sources:

- <https://csrc.nist.gov/Projects/risk-management/sp800-53-controls/downloads>
- <https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53Ar5.pdf>

Planning use: separation of duties, least privilege, attributable audit, and
assessment methods inform reviewer independence, administrator boundaries,
department isolation, and generated validation. These publications do not
make H-CAM compliant without an applicable control baseline and assessment.

### NIST Privacy Framework And Minimization

Sources:

- <https://www.nist.gov/privacy-framework>
- <https://csrc.nist.gov/glossary/term/minimization>

Planning use: browser projections are purpose-bound and field-minimized. Raw
provider responses, unnecessary source attributes, credentials, destinations,
and protected identifiers do not enter the P5.4 browser contract.

## Spatial Data

### RFC 7946 GeoJSON

Source: <https://www.rfc-editor.org/info/rfc7946/>

Planning use: generated spatial projections use GeoJSON and WGS 84
longitude/latitude ordering with explicit precision and bounds.

### OGC API Features

Source: <https://ogcapi.ogc.org/features/index.html>

Planning use: spatial data is exposed as bounded queryable features rather
than an unbounded client dataset. This plan makes no OGC conformance claim.

## Graph Dependency Research

### React Flow Accessibility

Source: <https://reactflow.dev/learn/advanced-use/accessibility>

Planning use: React Flow exposes keyboard focus, selection, ARIA roles, labels,
and localized accessibility text. Those features make it the recommended
candidate for a bounded read-only enhanced graph, subject to exact version and
supply-chain approval. Its editing defaults must be disabled.

### Cytoscape.js

Source: <https://js.cytoscape.org/>

Planning use: Cytoscape provides a mature graph model, layouts, extensions, and
headless operation. Its graph algorithms are not needed in the browser and
could blur the no-client-inference boundary, so it remains a fallback option.

### Sigma.js

Source: <https://www.sigmajs.org/docs/advanced/renderers/>

Planning use: WebGL rendering is relevant to future very-large bounded graph
profiles, but it is not justified for the initial table-authoritative P5.4
scope. Accessibility and complexity costs require a later measured decision.

## Research Conclusions

1. Human review must have information, authority, independence, and an actual
   ability to reject or abstain; a confirmation button alone is insufficient.
2. Exact provenance, revision, evidence roles, limitations, and correction
   lineage are more defensible than a natural-language explanation alone.
3. Strong conditional requests and explicit idempotency receipts are required
   for review and lifecycle mutations.
4. Events should invalidate; HTTP should confirm.
5. Graphs and maps are useful projections, but bounded tables remain the
   accessible and semantic authority.
6. Field minimization and department isolation are enforced before browser
   projection, not by hiding DOM elements.
7. Generated-only validation can prove deterministic consumer behavior but not
   legal compliance, human-review quality, model validity, or operational
   readiness.
