# h-cam-2.0
mayank repo of h cam experiment

## Phase 3 AI analytics

Phase 3 planning defines anonymous detection, per-camera tracking, line/zone
events, synthetic ANPR, runtime selection, data/model governance, security, and
validation. The authorized P3.0 foundation now adds model-independent contracts,
deterministic fixtures, prohibited-data guardrails, and a durable assignment
control plane with RBAC, ETags, revisions, audit, and transactional outbox.
P3.2 adds an accepted, default-off generated-input detector reference. P3.3 adds
an accepted, generated-only anonymous stream-local tracker under
`D-P3.3-ACCEPTANCE`. P3.4 is implemented, technically validated, and accepted
under `D-P3.4-ACCEPTANCE` for its exact historical package digest.
P3.5 synthetic-ANPR planning is authorized under `D-P3.5-PLAN-AUTH`. The exact
`A/A/A/A` technical baseline is approved, and `D-P3.5-ARTIFACT-RESEARCH`
authorized exactly seven quarantine downloads. Their evidence packet is owner
accepted. `D-P3.5-RUNTIME-RESEARCH` authorized only isolated dependency, SBOM,
license, vulnerability, scan, and import research outside the worktree. That
evidence is complete. The owner has now confirmed `D-P3.5-START`, authorizing only the
digest-bound, generated-only, default-off local implementation slice with five
loadable artifacts, two blocked Tesseract artifacts, and zero network actions.
`P35-W1` contracts, the visible non-issuable `SYN` token policy, and recursive
prohibited-input/zero-retention guardrails are now implemented and validated.
`P35-W3` deterministic ephemeral token generation and token-free sealed split
manifests are also implemented and validated; `P35-W2` remains blocked.
None of these milestones adds a real CCTV media path.

A metadata-only [P3.5 artifact review proposal](docs/phase-3/p3-5-artifact-review-proposal.md)
pins the recommended artifact locations and bounds. The separate
[artifact research authorization](docs/phase-3/p3-5-artifact-research-authorization.md)
permits only its seven exact external artifacts to enter a non-runtime local
quarantine; it authorizes no extraction, execution, or implementation.
The [runtime research authorization](docs/phase-3/p3-5-runtime-research-authorization.md)
separately bounds external Python dependency evidence work. Its
[runtime evidence](docs/phase-3/p3-5-runtime-research-evidence.md) records the
exact non-runtime closure and remaining blocks. The
[P3.5 start authorization](docs/phase-3/p3-5-start-authorization.md) records the
exact implementation allowlist and continuing prohibitions. The
[P3.5 W1 contracts and guardrails](docs/phase-3/p3-5-w1-contracts-guardrails.md)
record the first bounded implementation slice. The
[P3.5 W3 deterministic generator and sealed splits](docs/phase-3/p3-5-w3-generator-splits.md)
record the next authorized local generated-only slice.

P3.1 planning and its generated-only implementation boundary are authorized
under `D-P3.1-001`. The technical evidence package is implemented and verifies
with zero failures. Clean-source regeneration is complete, and `mayank-admin`
accepted the exact evidence package under `D-P3.1-ACCEPTANCE`. P3.2 is accepted
under `D-P3.2-ACCEPTANCE`, and P3.3 is accepted under
`D-P3.3-ACCEPTANCE`. Cameras, real media, external datasets, identity,
cross-camera linkage, operational alerts, production use, and deployment remain
unauthorized.

Start here: [docs/phase-3/README.md](docs/phase-3/README.md)

Contract snapshots and their review workflow are documented in
[contracts/phase-3/README.md](contracts/phase-3/README.md).

Generate the machine-readable P3.0 readiness report without activating any
analytics runtime:

```powershell
uv run --locked --extra dev python tools/phase3_readiness.py
uv run --locked --extra dev python tools/phase3_readiness.py --json
uv run --locked --extra dev python tools/phase31_readiness.py --strict
uv run --locked --extra dev python tools/phase31_readiness.py --json --strict
uv run --locked --extra dev python tools/phase31_contracts.py check --require-clean-source
uv run --locked --extra dev python tools/phase31_implementation_readiness.py --json --strict
uv run --locked --extra dev python tools/phase32_entry_readiness.py --json
uv run --locked --extra dev --extra analytics python tools/phase32_implementation_readiness.py
uv run --locked --extra dev --extra analytics python tools/phase33_tracking_evidence.py check
uv run --locked --extra dev --extra analytics python tools/phase33_sbom.py check
uv run --locked --extra dev --extra analytics python tools/phase33_implementation_readiness.py --require-clean-source --require-acceptance --json
uv run --locked --extra dev python tools/phase34_readiness.py --strict --json
uv run --locked --extra dev --extra analytics python tools/phase34_c10_evidence.py check
uv run --locked --extra dev --extra analytics python tools/phase34_supply_chain.py check
uv run --locked --extra dev --extra analytics python tools/phase34_implementation_readiness.py --require-clean-source --require-acceptance --json
uv run --locked --extra dev python tools/phase35_readiness.py --strict --json
uv run --locked --extra dev python tools/phase35_contracts.py check
uv run --locked python tools/phase35_artifact_research.py --all --root 'E:\h-cam-research-cache\phase-3\p3-5'
uv run --locked python tools/phase35_artifact_inspect.py --root 'E:\h-cam-research-cache\phase-3\p3-5'
uv run --locked --extra dev python tools/phase35_runtime_research.py all --root 'E:\h-cam-research-cache\phase-3\p3-5-runtime'
```

The P3.3 readiness command should report `accepted` with zero technical
failures and zero manual gates while the exact historical package acceptance
record remains valid.

The P3.4 entry command should report
`implementation_authorized_generated_only`, zero technical failures, and zero
manual gates. That authorization permits bounded implementation work but does
not grant final acceptance.

The P3.4 implementation verifier should report `accepted`, zero technical
failures, and zero manual gates while preserving the immutable historical
package binding. The PostGIS validation image remains deployment-blocked.

The P3.5 planning verifier should report
`implementation_authorized_generated_only_staged`, zero technical failures,
and zero manual gates. It verifies the approved `A/A/A/A`
baseline, exact artifact acceptance, completed restricted runtime evidence,
digest-bound generated-only start authorization, and the exact W1-only
and W3-only application boundary. The verifier itself performs no download, extraction,
synthetic generation, training, inference, media access, or model execution.
The artifact-research command is separately gated and writes only the seven
authorized files and receipts to the external local quarantine.

## Phase 2 camera and video ingestion

Phase 2 adds stream endpoint management, metadata-only health workers, a
controlled ONVIF simulator, authenticated background capability inventory,
short-lived HLS authorization, and a disposable 50-stream synthetic lab. It
does not discover camera networks, control cameras, capture images, or record
video.

Start here: [docs/phase-2/README.md](docs/phase-2/README.md)

The accepted Phase 2 OpenAPI and database snapshots remain preserved in
[contracts/phase-2/README.md](contracts/phase-2/README.md); the additive current
baseline is under `contracts/phase-3/`.

```powershell
python tools/phase2_lab.py prepare
python tools/phase2_lab.py config
python tools/phase2_lab.py start
python tools/phase2_lab.py verify --timeout 360
python tools/phase2_lab.py stop
```

Capability refresh is opt-in for each ONVIF stream. The worker and detailed
contract are documented in
[ONVIF capability management](docs/phase-2/capability-management.md):

```powershell
hcam capability-worker --once
hcam capability-worker --poll-seconds 5
```

## Phase 1 camera registry backend

Phase 1 begins with the normalized camera registry, stream-state contract,
health endpoints, local SQLite database, migration, and import audit trail.

Start here: [docs/phase-1/README.md](docs/phase-1/README.md)

```powershell
uv sync --locked --extra dev
$env:HCAM_DATABASE_URL = "sqlite:///./var/hcam.db"
$env:HCAM_ENVIRONMENT = "development"
$env:HCAM_DEV_AUTH_ENABLED = "true"
uv run --locked --extra dev alembic upgrade head
uv run --locked --extra dev hcam import-registry tests/fixtures/camera-registry-seed.json
uv run --locked --extra dev python -m uvicorn hcam.main:app --reload
```

The synthetic seed above is for local development only. OpenAPI is available
at `http://127.0.0.1:8000/docs` after startup.

Registry endpoints require explicit local development identity headers. See
[Phase 1 security and management](docs/phase-1/security-and-management.md) for
the role matrix, write API, ETag, audit, and production identity boundaries.
See [Phase 1 build and test](docs/phase-1/build-and-test.md) for the interpreter
matrix, coverage, lint, migration, dependency-audit, and artifact checks.
See [Phase 1 operations and observability](docs/phase-1/operations-and-observability.md)
for request IDs, metadata-only access events, SQLite backup/recovery,
PostgreSQL integration, protected Prometheus metrics, synthetic performance,
and concurrent load smokes. See
[Phase 1 service objectives](docs/phase-1/service-objectives.md) for metric
labels, regression objectives, and the Grafana dashboard, and
[deployment validation](deploy/README.md) for the non-root container stack.

Local SQLite recovery commands never overwrite existing files:

```powershell
.\.venv\Scripts\hcam backup-database .\backups\hcam-phase1.db
.\.venv\Scripts\hcam verify-backup .\backups\hcam-phase1.db
.\.venv\Scripts\hcam restore-backup .\backups\hcam-phase1.db .\var\hcam-restored.db
.\.venv\Scripts\hcam recovery-drill .\backups\drill-001
```

## Phase 0 foundation

Phase 0 defines the H-CAM product baseline, requirements, architecture,
governance, validation gates, and Phase 1 entry plan.

Start here: [docs/phase-0/README.md](docs/phase-0/README.md)

## Sentinel CCTV environment probe

This repository includes a safe, read-only probe for the Sentinel Gujarat CCTV
reference environment. It is for development planning and stream compatibility
checks only; it does not bulk-download CCTV footage.

```powershell
python tools/sentinel_cctv_probe.py metadata
python tools/sentinel_cctv_probe.py state --camera-id 1
python tools/sentinel_cctv_probe.py stream-test --camera-id 1
python tools/sentinel_cctv_probe.py snapshot
python tools/sentinel_cctv_probe.py offline-summary
python tools/sentinel_cctv_probe.py registry-export --output fixtures/sentinel/registry-seed.json
python tools/sentinel_cctv_probe.py all
```

Default target: `https://live.sentinelgujarat.in`

Offline regression checks:

```powershell
python -m py_compile tools/sentinel_cctv_probe.py tools/phase0_readiness.py
python -m unittest discover -s tests -v
python tools/phase0_readiness.py --run-validation
```

See [docs/phase-0/cctv-environment.md](docs/phase-0/cctv-environment.md) for
the observed API shape, safety rules, and test workflow.

See [docs/phase-0/readiness-report.md](docs/phase-0/readiness-report.md) for
the completed Phase 0 evidence map.
