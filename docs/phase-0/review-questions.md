# Review Questions

These questions should be answered before Phase 1 coding starts.

## Product Scope

- Are Command Center, Operations Center, Intelligence Center, Data Platform,
  Admin Center, Cyber Security Center, and Developer Portal still the intended
  product surfaces?
- Should Phase 1 remain backend-only, or should a minimal admin/operator UI
  skeleton start in parallel?
- Which users should be prioritized first: operator, investigator, admin, or
  command officer?

## Data And Authorization

- Can the attached official PDFs now be read and treated as requirements
  evidence?
- Which authenticated organizer resources and APIs become available after the
  project owner signs in?
- Are any Government database integrations separately authorized, or should
  they remain interface-ready simulations?
- What retention rules apply to clips, frames, metadata, model outputs, and
  evidence exports?
- Who approves sensitive data use?

Official portal answers already captured:

- The sandbox uses approximately 12 hours from each of 50 cameras across five
  departments, replayed as synchronized simulated-live streams.
- Teams may create representative watchlist data for the demonstration.
- The public portal does not grant production CCTV or real Government database
  access, so those integrations remain blocked.

## Technical Direction

- Is Python/FastAPI acceptable for the first backend foundation?
- Should Phase 1 stay single-repo in `h-cam-2.0`?
- Is SQLite acceptable for initial laptop development before PostgreSQL?
- Should registry import use generated fixture files, a checked sample fixture,
  or both?
- Should API contracts be documented as OpenAPI first, or generated from code?
- Should PostGIS be introduced in Phase 1, or should SQLite retain validated
  latitude/longitude fields until the GIS phase?

## Team Workflow

- Who owns backend, AI, frontend, infrastructure, data/GIS, and product docs?
- Will tasks live in GitHub Issues, Linear, Notion, or another system?
- What branch naming and PR review policy should the six-person team use?
- What is the minimum CI gate before merge?

## Demo Direction

- What must be shown in the first demo: camera registry, live stream probe,
  dashboard, AI detection, alerts, or investigation search?
- What must never be shown or stored in demo material?

Official portal answers already captured:

- The challenge requires working demonstrations on both participant-owned feeds
  and Government-provided sandbox feeds.
- Mock-ups, animations, and concept-only videos are not accepted as working
  demonstrations.
