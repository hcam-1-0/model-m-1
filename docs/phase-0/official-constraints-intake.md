# Official Constraints Intake

This document tracks challenge rules, dataset constraints, and authorization
evidence for H-CAM Phase 0. It is intentionally conservative: public news
coverage can guide planning, but only official materials should authorize
sensitive integrations, live-feed usage, government datasets, watchlists, or
submission claims.

## Source Status

Current status: official source intake is not complete.

The user previously instructed the assistant not to read the attached official
PDF files for now. Until that changes, this repository should treat the
attached official PDFs as available but unread evidence.

Gate label: attached official PDF files.

## Public Source Scan

Checked on: 2026-08-18.

| Source | URL | Planning Signal | Approval Strength |
| --- | --- | --- | --- |
| Live Sentinel CCTV reference page | `https://live.sentinelgujarat.in/` | Page presents a CCTV control room surface. The repository uses this only through safe metadata/state/stream probes. | Reference environment only |
| IANS report, 2026-08-17 | `https://ianslive.in/gujarat-police-plans-single-network-for-80000-cctv-cameras-through-ai-based-hackathon--20260817133755` | Reports 80,000+ camera integration, AI video analytics, live-feed testing, two-stage challenge structure, top-six finale, Rs 37 lakh prize pool, and Sentinel portal for details. | Public reporting, not final rules |
| The New Indian Express report, 2026-08-17 | `https://www.newindianexpress.com/states/gujarat/2026/Aug/17/gujarat-police-to-host-indias-largest-cctv-integration-ai-hackathon` | Reports 80,000+ cameras, real-world policing scenarios, ANPR, vehicle tracking, watchlist matching, cross-camera search, two categories, top-six production demo, and official portal reference. | Public reporting, not final rules |
| RTIH challenge listing | `https://challenges.rtih.co.in/challenge/spic` | Page loaded with generic challenge shell and no usable H-CAM rules at time of check. | Not enough evidence |
| Official Sentinel rules portal reference | `https://sentinel.gujarat.gov.in` | Public reports say participation details, eligibility, rules, and guidelines are available there. The exact official rules still need capture. | Pending official capture |

## Planning Facts To Verify

The following items are useful for planning, but must be confirmed from
official challenge materials before they become binding project requirements.

- Gujarat Police Innovation Challenge 2026 targets integration of more than
  80,000 CCTV cameras.
- The challenge focuses on heterogeneous CCTV systems across departments,
  vendors, video management systems, and network architectures.
- The expected capability set includes real-time detection of suspicious
  persons, vehicles, and unusual activities.
- Expected analytics include ANPR, vehicle tracking, watchlist matching, and
  cross-camera search.
- The challenge is reported as two-stage: an open innovation stage followed by
  a finale for top teams.
- The finale is reported as a live production environment demonstration using
  real-world policing scenarios.
- Total prizes are reported as Rs 37 lakh.
- Reported partners include i-Hub Gujarat, DA-IICT, and NFSU.

## Required Official Answers

These questions must be answered before Phase 1 uses sensitive data or presents
claims as official.

### Eligibility And Participation

- Which categories can participate?
- Does H-CAM belong under student/small startup, larger startup/company, or
  another category?
- Are there registration, DPIIT, incorporation, team-size, or residency rules?
- Are there deadlines, abstract formats, demo formats, or mandatory templates?

### Dataset And CCTV Access

- What CCTV feeds, sample clips, or datasets are officially allowed?
- Are participants allowed to probe live reference streams?
- Is bulk video download prohibited, limited, or governed by a separate
  agreement?
- Are generated snapshots, metadata, or stream probes allowed to be stored
  locally?
- Are official datasets downloadable, streamed only, sandboxed, or supplied at
  the finale?

### Sensitive Data

- Are government database integrations permitted in the prototype?
- Are watchlists allowed, and if yes, must they be synthetic?
- Are facial recognition, person re-identification, biometric matching, vehicle
  owner lookup, or police record matching allowed?
- What masking, retention, consent, audit, and access-control rules apply?
- Who is the approving authority for sensitive data use?

### Demo And Submission

- What must be demonstrated in Stage 1?
- What must be demonstrated in the finale?
- Can Sentinel reference streams be shown in a recorded demo?
- Must demo footage be synthetic, official, or generated from provided
  scenarios?
- What claims are prohibited in portfolio, website, presentation, or video?

### Security And Compliance

- Are there required security controls, NDAs, audit rules, or vulnerability
  disclosure requirements?
- Are teams allowed to connect external cloud services, LLM APIs, or third-party
  model providers?
- Are there data residency, encryption, access log, or retention requirements?
- Are there restrictions on storing logs, thumbnails, embeddings, or model
  outputs?

## Current Phase 0 Policy

Until official answers are captured:

- Do not commit CCTV video, frames, clips, credentials, cookies, government data,
  police records, watchlists, owner details, or personally sensitive data.
- Treat Sentinel only as a reference environment for metadata/state and
  metadata-only stream probing.
- Treat all watchlist, government database, biometric, owner-detail, and police
  record features as simulated or blocked.
- Label demo data as synthetic unless it comes from an explicitly authorized
  official source.
- Do not claim official compliance, official deployment readiness, or official
  data access based only on public news coverage.

## Intake Completion Checklist

- [ ] Official challenge rules captured from `https://sentinel.gujarat.gov.in`.
- [ ] Attached official PDFs reviewed after user approval to read them.
- [ ] Eligibility and category rules recorded.
- [ ] Dataset and live-feed access rules recorded.
- [ ] Sensitive-data and government-database policy recorded.
- [ ] Demo/submission rules recorded.
- [ ] Security/compliance requirements recorded.
- [ ] Conflicts between public reporting and official documents resolved.
- [ ] Phase 0 acceptance checklist updated only after official evidence exists.
