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

- What official datasets are allowed for the hackathon or challenge submission?
- Can the attached official PDFs now be read and treated as requirements
  evidence?
- Are any government database integrations authorized now, or only simulated?
- Are watchlists allowed in the demo, and if yes, must they be synthetic?
- What retention rules apply to clips, frames, metadata, model outputs, and
  evidence exports?
- Who approves sensitive data use?

## Technical Direction

- Is Python/FastAPI acceptable for the first backend foundation?
- Should Phase 1 stay single-repo in `h-cam-2.0`?
- Is SQLite acceptable for initial laptop development before PostgreSQL?
- Should registry import use generated fixture files, a checked sample fixture,
  or both?
- Should API contracts be documented as OpenAPI first, or generated from code?

## Team Workflow

- Who owns backend, AI, frontend, infrastructure, data/GIS, and product docs?
- Will tasks live in GitHub Issues, Linear, Notion, or another system?
- What branch naming and PR review policy should the six-person team use?
- What is the minimum CI gate before merge?

## Demo Direction

- Will the demo use Sentinel reference streams, synthetic video, uploaded test
  clips, or an official sandbox?
- What must be shown in the first demo: camera registry, live stream probe,
  dashboard, AI detection, alerts, or investigation search?
- What must never be shown or stored in demo material?
