# P3.4 Third-Party Notices

This inventory records the direct P3.4 dependencies and the existing analytics
dependency reused by P3.4. Exact artifacts and hashes are in
`contracts/phase-3/p3-4-dependencies.json`; the deterministic CycloneDX record
is `contracts/phase-3/p3-4-sbom.cdx.json`.

| Component | Version | Role | License | Source |
| --- | --- | --- | --- | --- |
| Shapely | 2.1.2 | Image-space geometry and predicates | BSD-3-Clause | https://github.com/shapely/shapely |
| GEOS | 3.13.1 local wheel; 3.14.1 PostGIS | Native geometry engine | LGPL-2.1-or-later | https://libgeos.org/ |
| cel-expr-python | 0.1.3 | Constrained CEL parse/type-check/evaluation | Apache-2.0 | https://github.com/cel-expr/cel-python |
| PostgreSQL | 18.6 in validation image | Authoritative database | PostgreSQL | https://www.postgresql.org/ |
| PostGIS | 3.6.4 in validation image | Authoritative spatial type, checks, and index | GPL-2.0-or-later | https://postgis.net/ |
| PROJ | 9.8.1 in validation image | PostGIS native dependency; no H-CAM geographic claim | MIT | https://proj.org/ |
| NumPy | 2.5.2 | Existing analytics/native array dependency | BSD-3-Clause and bundled notices | https://github.com/numpy/numpy |
| Hypothesis | 6.165.10 | Development property/state tests only | MPL-2.0 | https://github.com/HypothesisWorks/hypothesis |

Transitive package licenses remain governed by their upstream distributions
and the recorded SBOM. This file is an engineering inventory, not legal advice.

## Vulnerability Boundary

The Python audit checked 76 installed packages and found no known
vulnerabilities at validation time. That result is time-bound and does not
replace future scanning.

The exact `postgis/postgis:18-3.6-alpine` validation image has unresolved
findings recorded without suppression in
`p3-4-container-vulnerability-review.json`. Its deployment gate is
`blocked_pending_cleaner_image_or_remediation_and_rescan`.

No ONVIF, OGC, CEL, model, safety, or product conformance certification is
claimed by this implementation.
