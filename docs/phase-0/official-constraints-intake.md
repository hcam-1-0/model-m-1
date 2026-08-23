# Official Constraints Intake

This document records the official Gujarat Police Innovation Challenge 2026
constraints that shape H-CAM. It separates published challenge requirements
from permissions that have not been granted.

## Source Status

Current status: official public portal intake is complete for Phase 0 planning.

Checked on: 2026-08-18.

The public pages at `https://sentinel.gujarat.gov.in` now provide enough
official evidence to define the challenge architecture, participant categories,
test environment, deliverables, evaluation areas, schedule, and conservative
data-use boundary. This satisfies the Phase 0 official-source planning gate.

It does not authorize access to production CCTV, Government databases, police
records, biometric systems, or private portal resources. The attached official
PDF files remain unread because the user instructed the assistant to skip them.
Authenticated resources and any later organizer instructions must be reviewed
before they are used.

Live tracking issue: https://github.com/mayankthakor227/h-cam-2.0/issues/11

## Official Source Snapshot

| Official Source | Captured Requirement |
| --- | --- |
| [Home](https://sentinel.gujarat.gov.in/) | Real-world CCTV integration challenge, official dataset, registration, and core platform objectives |
| [About](https://sentinel.gujarat.gov.in/about) | Eligible participant types, open-source technology expectation, objectives, and organizer details |
| [Problem Statements](https://sentinel.gujarat.gov.in/problems) | Mandatory integration model, detailed architecture, test case, deliverables, scale plan, and evaluation framework |
| [FAQs](https://sentinel.gujarat.gov.in/faqs) | Fifty-camera dataset details, eligibility categories, working-demo rules, submission links, and official clarifications |
| [Phases And Prizes](https://sentinel.gujarat.gov.in/phases) | Sandbox and production rounds, finalist structure, category structure, and prize breakdown |
| [Schedule](https://sentinel.gujarat.gov.in/schedule) | Registration, shortlisting, event, and result dates |
| [Registration](https://sentinel.gujarat.gov.in/register) | Registration roles and account-level registration requirements |

Public news reports remain useful corroboration, but the portal pages above are
the Phase 0 source of truth where the two differ.

## Confirmed Challenge Requirements

### Architecture And Integration Model

- Model 1, Centralised CCTV Registry and GIS Foundation, is compulsory for all
  submissions.
- Model 1 must be combined with one or more of Model 2, Model 3, Model 4, or a
  hybrid/custom architecture because registry metadata alone does not provide
  feed integration, viewing, or analytics.
- The architecture must be open, modular, scalable, secure, standards-based,
  vendor-neutral, and adapter-oriented.
- The target environment spans 26 Government departments, mixed analog and IP
  cameras, multiple VMS vendors and protocols, geographically dispersed sites,
  and differing storage/retention systems.
- The scale plan must address approximately 80,000 cameras.
- Suggested technology stacks are references rather than exclusive choices,
  but the portal states that solutions should use open-source technologies.

### Mandatory Model 1 Capability

The registry foundation must plan for:

- bulk, manual, and API-based camera onboarding
- camera identity, department, ownership, type, location, connectivity, storage,
  health, and maintenance metadata
- GIS mapping and layered filtering
- role-based search, filtering, export, and metadata audit trails
- gap analysis for uncovered areas and ageing infrastructure
- documented registry APIs

This confirms H-CAM's registry-first Phase 1 direction, but GIS-ready fields
must be included in the domain contract even if the first phase is backend-only.

### Dataset And Technical Test

- The sandbox dataset is described as approximately 12 hours of CCTV footage
  from each of 50 cameras across Health, Police, GSRTC, Panchayat, and Municipal
  Corporation departments.
- Recorded footage is synchronized on a common timeline and served as simulated
  live video through a dedicated streaming endpoint for each camera.
- The simulation protects production infrastructure and gives teams a
  repeatable, consistent test environment.
- Teams must onboard the provided cameras, provide centralized monitoring and
  analytics, and trace a designated vehicle across camera locations using the
  registration number supplied during evaluation.
- Expected output includes a timestamped, location-wise route history and
  evidence of onboarding, interoperability, analytics, and end-to-end behavior.
- The problem page permits teams to create their own representative watchlist
  database for demonstrating continuous matching and real-time alerts.

The public portal does not grant direct access to production CCTV or real
Government watchlists. The existing `live.sentinelgujarat.in` probe remains a
reference environment tool and must not be described as production access.

### Eligibility And Categories

- Category 1 includes students, graduates, postgraduates, doctoral scholars,
  academic/research teams, and DPIIT-recognized startups.
- A startup entering Category 1 must provide a valid DPIIT Startup Recognition
  Certificate at registration or verification.
- Category 2 includes companies, system integrators, technology providers,
  LLPs, partnerships, and other established enterprises not eligible as a
  DPIIT-recognized Category 1 startup.
- The registration page offers Student/Student Team/Researchers/Professionals,
  DPIIT Startup, and Company/SI registration roles.

The project owner must select the actual H-CAM registration identity and retain
the supporting student, DPIIT, or company evidence outside this repository.

### Official Schedule

- Registration opened: 4 August 2026.
- Last date to apply: 29 August 2026.
- Shortlisting announcement: 30 August 2026.
- Hackathon event at i-Hub Gujarat: 1-2 September 2026.
- Results and prize distribution: 2 September 2026.

### Submission And Demonstration

- Submit a solution presentation in PPT or PDF form.
- Submit a technical proposal/high-level design covering architecture,
  heterogeneous integration, deployment, analytics, cybersecurity, scale, and
  department-level information needs.
- Provide a 2-3 minute working demonstration on the participant's own feed that
  shows onboarding, live or recorded viewing, and vehicle detection/ANPR.
- Provide a working demonstration on the Government-provided feed showing
  onboarding, viewing, and analytics output, with a screen recording and output
  report containing detections and timestamps.
- Mock-ups, animations, and concept-only videos are not accepted as the working
  demonstration.
- Submission can use an unlisted YouTube link or a viewer-enabled Google Drive
  or OneDrive link. A hosted URL with test credentials and a GitHub/GitLab
  source link may also be provided.

### Evaluation And Scale

The official evaluation areas are:

- successful Government-feed test case
- solution presentation and model justification
- technical architecture and HLD quality
- maturity of the working platform
- quality of video analytics and reports
- scalability and proof-of-concept readiness for approximately 80,000 cameras
- submission completeness

The scale plan must cover central, regional, and edge compute; GPU/accelerator
capacity; bandwidth and low-bandwidth operation; hot/warm/cold storage;
horizontal scaling; observability; high availability; backup; disaster
recovery; phased rollout; and estimated implementation/operational costs.

Bonus capabilities do not replace mandatory requirements.

## Sensitive Data And Authorization Boundary

The official challenge asks for integration readiness with VAHAN, SARTHI,
eGujCop/CCTNS, AFIS, and NAFIS and describes watchlist-driven alert scenarios.
That product requirement is not evidence that H-CAM currently has credentials,
data access, or permission to copy those records.

Until the organizer supplies authorized access and handling instructions:

- Do not commit CCTV video or sensitive records to the repository.
- Treat every real government database integration as blocked until separate
  credentials, purpose, access scope, and handling rules are approved.
- use only organizer-provided sandbox feeds under their published terms
- use synthetic or team-created representative watchlist records
- do not commit CCTV video, frames, clips, credentials, Government data, police
  records, real watchlists, vehicle owner details, or biometric data
- do not query VAHAN, SARTHI, eGujCop/CCTNS, AFIS, or NAFIS
- do not claim production CCTV access or official deployment approval
- keep logs, thumbnails, embeddings, model outputs, and exports free of
  personally sensitive data unless a later approved policy governs them
- retain auditability, least privilege, encryption, network segmentation, and
  role-based access as mandatory architecture requirements

Demo data must be labelled according to its actual source. Team-created data is
synthetic/representative; organizer-provided sandbox data is official challenge
test data; neither should be presented as live production police data.

## Remaining Unverified Inputs

- The attached official PDF files have not been read.
- Authenticated portal resources, API documentation, stream credentials, and
  submission forms have not been accessed.
- The portal's Terms and Conditions and Privacy Policy were not exposed as
  usable public links during this review.
- Any NDA, participant agreement, resource-specific license, retention rule,
  or later jury instruction must be captured when officially provided.
- The project owner has not yet selected the H-CAM participant category.

These items do not block registry-first planning. They do block use of private
resources, sensitive integrations, and final submission claims where the later
terms are material.

## Intake Completion Checklist

- [x] Official challenge pages captured from `https://sentinel.gujarat.gov.in`.
- [x] Eligibility and category rules recorded.
- [x] Dates and two-phase format recorded.
- [x] Mandatory Model 1 and hybrid architecture requirement recorded.
- [x] Dataset and simulated-live test conditions recorded.
- [x] Working-demo and submission requirements recorded.
- [x] Evaluation and scalability requirements recorded.
- [x] Conservative sensitive-data and Government-database boundary recorded.
- [x] Public reporting replaced by official portal evidence where available.
- [ ] Attached official PDFs reviewed after user approval to read them.
- [ ] Authenticated resource terms reviewed when project-owner access is used.
- [ ] H-CAM participant category selected by the project owner.

## Gate Conclusion

The official-source intake gate is satisfied for Phase 0 planning. Phase 1 may
design schemas and interfaces against these published requirements after owner
approval, but it must continue to block production feeds, real Government data,
biometrics, and real watchlists until separate authorization evidence exists.
