from __future__ import annotations

from dataclasses import dataclass

from hcam.acceptance.canonical import digest
from hcam.acceptance.claims import build_registers
from hcam.acceptance.compatibility import (
    build_compatibility_matrix,
    compatibility_evidence_ref,
    validate_compatibility,
)
from hcam.acceptance.contracts import (
    ClaimRegisterV1,
    CompatibilityMatrixV1,
    EventWorkflowCatalogueV1,
    HttpCatalogueV1,
    LimitationRegisterV1,
    OperationsRunbookV1,
    ProductionPrerequisiteOutlineV1,
    ReconstructionManifestV1,
    ScenarioManifestV1,
    UiAccessibilityCatalogueV1,
)
from hcam.acceptance.fixtures import build_manifest
from hcam.acceptance.handoff import (
    build_event_workflows,
    build_http_catalogue,
    build_ui_accessibility,
    validate_handoff,
)
from hcam.acceptance.projections import build_projection_bundle
from hcam.acceptance.replay import (
    PortfolioResult,
    build_reconstruction_manifest,
    run_portfolio,
)
from hcam.acceptance.runbooks import (
    build_generated_runbook,
    build_production_prerequisites,
    validate_non_operational,
)
from hcam.acceptance.scenarios import ScenarioEngine


@dataclass(frozen=True, slots=True)
class AcceptanceBundle:
    manifest: ScenarioManifestV1
    portfolio: PortfolioResult
    reconstructions: tuple[ReconstructionManifestV1, ...]
    claims: ClaimRegisterV1
    limitations: LimitationRegisterV1
    runbook: OperationsRunbookV1
    production_prerequisites: ProductionPrerequisiteOutlineV1
    http: HttpCatalogueV1
    events: EventWorkflowCatalogueV1
    ui: UiAccessibilityCatalogueV1
    compatibility: CompatibilityMatrixV1
    projections: dict[str, dict[str, object]]

    @property
    def complete(self) -> bool:
        return self.portfolio.complete

    @property
    def canonical_digest(self) -> str:
        return digest(
            {
                "manifest": self.manifest,
                "runs": self.portfolio.runs,
                "comparisons": self.portfolio.comparisons,
                "reconstructions": self.reconstructions,
                "claims": self.claims,
                "limitations": self.limitations,
                "runbook": self.runbook,
                "production_prerequisites": self.production_prerequisites,
                "http": self.http,
                "events": self.events,
                "ui": self.ui,
                "compatibility": self.compatibility,
                "projections": self.projections,
            },
            maximum_bytes=16_777_216,
        )


class GeneratedAcceptanceService:
    """Default-off facade for bounded generated P4.7 validation."""

    def __init__(
        self, *, enabled: bool = False, environment: str = "development"
    ) -> None:
        self.engine = ScenarioEngine(enabled=enabled, environment=environment)

    def build_manifest(self) -> ScenarioManifestV1:
        return build_manifest()

    def execute(self) -> AcceptanceBundle:
        manifest = self.build_manifest()
        portfolio = run_portfolio(self.engine, manifest)
        reconstructions = tuple(
            build_reconstruction_manifest(run)
            for run in portfolio.runs
            if run.replay_index == 1
        )
        support = (compatibility_evidence_ref(),)
        claims, limitations = build_registers(support)
        runbook = build_generated_runbook()
        prerequisites = build_production_prerequisites()
        validate_non_operational(runbook, prerequisites)
        http = build_http_catalogue()
        events = build_event_workflows()
        ui = build_ui_accessibility()
        validate_handoff(http, events, ui)
        compatibility = build_compatibility_matrix(compatibility_evidence_ref())
        validate_compatibility(compatibility)
        projections = build_projection_bundle(http, events, ui)
        return AcceptanceBundle(
            manifest=manifest,
            portfolio=portfolio,
            reconstructions=reconstructions,
            claims=claims,
            limitations=limitations,
            runbook=runbook,
            production_prerequisites=prerequisites,
            http=http,
            events=events,
            ui=ui,
            compatibility=compatibility,
            projections=projections,
        )
