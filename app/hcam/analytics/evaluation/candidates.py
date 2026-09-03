from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Annotated, Literal, NamedTuple

from pydantic import Field, model_validator

from hcam.analytics.evaluation.contracts import (
    ApprovalRecordV1,
    ArtifactLicenseV1,
    CandidateArtifactManifestV1,
    Digest,
    DigestBoundRecord,
    ManifestReferenceV1,
    ResearchReferenceV1,
    ResolutionFieldV1,
    StableId,
    UtcDateTime,
    seal_record,
)


CAPTURED_ON = date(2026, 8, 24)
RECORDED_AT = datetime(2026, 8, 24, 12, 45, tzinfo=UTC)


class CandidateDefinition(NamedTuple):
    candidate_id: str
    role: str
    repository_key: str | None
    source_tier: Literal["S0", "S3"]
    code_license: str
    supported_taxonomy: tuple[str, ...]
    runtime_expectations: tuple[str, ...]
    export_expectations: tuple[str, ...]
    known_limits: tuple[str, ...]
    blockers: tuple[str, ...]


REPOSITORIES = {
    "yolox": {
        "url": "https://github.com/Megvii-BaseDetection/YOLOX",
        "title": "YOLOX official repository",
        "publisher": "Megvii BaseDetection",
        "commit": "6ddff4824372906469a7fae2dc3206c7aa4bbaee",
        "license": "Apache-2.0",
        "claim": "Repository documents YOLOX-Tiny and identifies its code license",
    },
    "dfine": {
        "url": "https://github.com/Peterande/D-FINE",
        "title": "D-FINE official repository",
        "publisher": "D-FINE authors",
        "commit": "956d1709314c2c6a4df6f34de232054578a7449f",
        "license": "Apache-2.0",
        "claim": "Paper-linked repository documents the D-FINE-N candidate",
    },
    "rfdetr": {
        "url": "https://github.com/roboflow/rf-detr",
        "title": "RF-DETR official repository",
        "publisher": "Roboflow",
        "commit": "47b37fe7283b2f79d0aa5af3e6ba9caf9b2a5e62",
        "license": "Apache-2.0",
        "claim": "Repository documents RF-DETR-S/L and component-specific licensing",
    },
    "bytetrack": {
        "url": "https://github.com/FoundationVision/ByteTrack",
        "title": "ByteTrack official repository",
        "publisher": "FoundationVision",
        "commit": "d1bf0191adff59bc8fcfeaa0b33d3d1642552a99",
        "license": "MIT",
        "claim": "Repository documents ByteTrack and its code license",
    },
    "paddleocr": {
        "url": "https://github.com/PaddlePaddle/PaddleOCR",
        "title": "PaddleOCR official repository",
        "publisher": "PaddlePaddle",
        "commit": "2661c7c0ef5c613e8f93c6e93b2e052399f0f854",
        "license": "Apache-2.0",
        "claim": "Repository documents PP-OCRv6 and PP-OCRv5 script models",
    },
    "tessdata-fast": {
        "url": "https://github.com/tesseract-ocr/tessdata_fast",
        "title": "Tesseract fast traineddata repository",
        "publisher": "Tesseract OCR",
        "commit": "87416418657359cb625c412a48b6e1d6d41c29bd",
        "license": "Apache-2.0",
        "claim": "Repository lists guj traineddata and its data license",
    },
    "tessdata-best": {
        "url": "https://github.com/tesseract-ocr/tessdata_best",
        "title": "Tesseract best traineddata repository",
        "publisher": "Tesseract OCR",
        "commit": "e12c65a915945e4c28e237a9b52bc4a8f39a0cec",
        "license": "Apache-2.0",
        "claim": "Repository lists high-accuracy guj traineddata and its data license",
    },
}

DETECTOR_TAXONOMY = (
    "object.person",
    "vehicle.bicycle",
    "vehicle.motorcycle",
    "vehicle.car",
    "vehicle.bus",
    "vehicle.truck",
    "object.unknown",
)

CANDIDATES = (
    CandidateDefinition(
        "DET-R0",
        "detector_reference",
        "yolox",
        "S3",
        "Apache-2.0",
        DETECTOR_TAXONOMY,
        ("onnxruntime-cpu-reference",),
        ("onnx-opset-unresolved",),
        (
            "No exact checkpoint, hash, export parity, or H-CAM slice result is recorded",
            "Upstream COCO labels require an approved H-CAM taxonomy mapping",
        ),
        (
            "exact-checkpoint-unresolved",
            "weight-license-unverified",
            "training-lineage-unverified",
            "model-card-unresolved",
            "sbom-unresolved",
        ),
    ),
    CandidateDefinition(
        "DET-E1",
        "detector_low_compute",
        "dfine",
        "S3",
        "Apache-2.0",
        DETECTOR_TAXONOMY,
        ("comparison-runtime-unresolved",),
        ("onnx-export-research-only",),
        (
            "D-FINE-N artifact identity and complete training provenance are unresolved",
            "Published accelerator results do not establish performance on H-CAM hardware",
        ),
        (
            "exact-checkpoint-unresolved",
            "weight-license-unverified",
            "training-lineage-unverified",
            "model-card-unresolved",
            "sbom-unresolved",
        ),
    ),
    CandidateDefinition(
        "DET-B1",
        "detector_balanced",
        "rfdetr",
        "S3",
        "Apache-2.0",
        DETECTOR_TAXONOMY,
        ("comparison-runtime-unresolved",),
        ("export-format-unresolved",),
        (
            "RF-DETR licensing is component-specific and must be verified for the exact S artifact",
            "No H-CAM dataset, slice, or resource evidence exists",
        ),
        (
            "exact-checkpoint-unresolved",
            "exact-weight-license-unverified",
            "training-lineage-unverified",
            "model-card-unresolved",
            "sbom-unresolved",
        ),
    ),
    CandidateDefinition(
        "DET-A1",
        "detector_accuracy",
        "rfdetr",
        "S3",
        "Apache-2.0",
        DETECTOR_TAXONOMY,
        ("comparison-runtime-unresolved",),
        ("export-format-unresolved",),
        (
            "RF-DETR licensing is component-specific and must be verified for the exact L artifact",
            "No H-CAM dataset, slice, or resource evidence exists",
        ),
        (
            "exact-checkpoint-unresolved",
            "exact-weight-license-unverified",
            "training-lineage-unverified",
            "model-card-unresolved",
            "sbom-unresolved",
        ),
    ),
    CandidateDefinition(
        "TRK-R0",
        "stream_local_tracker",
        "bytetrack",
        "S3",
        "MIT",
        (),
        ("stream-local-association-only",),
        ("no-model-export",),
        (
            "Tracker behavior depends on detector confidence and frame cadence",
            "Cross-camera identity and person re-identification are prohibited",
        ),
        (
            "exact-code-package-unresolved",
            "dependency-license-review-pending",
            "integration-lineage-unverified",
            "model-card-not-applicable-record-pending",
            "sbom-unresolved",
        ),
    ),
    CandidateDefinition(
        "OCR-L0",
        "ocr_latin_small",
        "paddleocr",
        "S3",
        "Apache-2.0",
        (),
        ("paddle-runtime-unresolved",),
        ("paddle-inference-format-unresolved",),
        (
            "PP-OCRv6 portfolio naming must map to an exact official artifact",
            "License-plate domain accuracy is unmeasured",
        ),
        (
            "exact-ppocrv6-small-artifact-unresolved",
            "weight-license-unverified",
            "training-lineage-unverified",
            "model-card-unresolved",
            "sbom-unresolved",
        ),
    ),
    CandidateDefinition(
        "OCR-L1",
        "ocr_latin_medium",
        "paddleocr",
        "S3",
        "Apache-2.0",
        (),
        ("paddle-runtime-unresolved",),
        ("paddle-inference-format-unresolved",),
        (
            "PP-OCRv6 portfolio naming must map to an exact official artifact",
            "License-plate domain accuracy is unmeasured",
        ),
        (
            "exact-ppocrv6-medium-artifact-unresolved",
            "weight-license-unverified",
            "training-lineage-unverified",
            "model-card-unresolved",
            "sbom-unresolved",
        ),
    ),
    CandidateDefinition(
        "OCR-D0",
        "ocr_devanagari",
        "paddleocr",
        "S3",
        "Apache-2.0",
        (),
        ("paddle-runtime-unresolved",),
        ("paddle-inference-format-unresolved",),
        (
            "Official documentation identifies devanagari_PP-OCRv5_mobile_rec",
            "Exact artifact license, hash, and plate-domain evidence remain unresolved",
        ),
        (
            "exact-devanagari-artifact-unresolved",
            "weight-license-unverified",
            "training-lineage-unverified",
            "model-card-unresolved",
            "sbom-unresolved",
        ),
    ),
    CandidateDefinition(
        "OCR-G0",
        "ocr_gujarati_fast",
        "tessdata-fast",
        "S3",
        "Apache-2.0",
        (),
        ("tesseract-lstm-runtime-unresolved",),
        ("tesseract-traineddata",),
        (
            "Fast integer model cannot be fine-tuned",
            "Exact guj traineddata hash and plate-domain evidence are unresolved",
        ),
        (
            "exact-guj-traineddata-unresolved",
            "runtime-version-unresolved",
            "training-lineage-unverified",
            "model-card-unresolved",
            "sbom-unresolved",
        ),
    ),
    CandidateDefinition(
        "OCR-G1",
        "ocr_gujarati_best",
        "tessdata-best",
        "S3",
        "Apache-2.0",
        (),
        ("tesseract-lstm-runtime-unresolved",),
        ("tesseract-traineddata",),
        (
            "Best traineddata trades speed for accuracy",
            "Exact guj traineddata hash and plate-domain evidence are unresolved",
        ),
        (
            "exact-guj-traineddata-unresolved",
            "runtime-version-unresolved",
            "training-lineage-unverified",
            "model-card-unresolved",
            "sbom-unresolved",
        ),
    ),
    CandidateDefinition(
        "PLATE-D0",
        "plate_region_detector",
        None,
        "S0",
        "proposed-internal",
        (),
        ("promoted-hcam-detector-family",),
        ("not-implemented",),
        (
            "No plate-region detector artifact exists",
            "Only generated or separately authorized plate-region data may be used",
        ),
        (
            "derived-artifact-not-implemented",
            "detector-family-not-promoted",
            "training-data-not-approved",
            "model-card-unresolved",
            "sbom-unresolved",
        ),
    ),
)


class SourceResearchDossierV1(DigestBoundRecord):
    digest_field = "dossier_digest"
    contract_type: Literal["hcam.analytics.source-research-dossier.v1"] = (
        "hcam.analytics.source-research-dossier.v1"
    )
    dossier_id: StableId
    dossier_digest: Digest
    captured_at: UtcDateTime
    method: Literal["official-metadata-only-no-download"] = (
        "official-metadata-only-no-download"
    )
    references: Annotated[list[ResearchReferenceV1], Field(min_length=1, max_length=32)]
    candidates: Annotated[list[ManifestReferenceV1], Field(min_length=1, max_length=32)]
    downloaded_artifacts: Annotated[list[StableId], Field(max_length=0)] = Field(
        default_factory=list
    )
    unresolved_blockers: Annotated[list[StableId], Field(min_length=1, max_length=256)]
    owner_decision_required_before_download: Literal[True] = True

    @model_validator(mode="after")
    def dossier_is_unique_and_download_free(self) -> SourceResearchDossierV1:
        reference_ids = [reference.reference_id for reference in self.references]
        candidate_ids = [candidate.record_id for candidate in self.candidates]
        if len(reference_ids) != len(set(reference_ids)):
            raise ValueError("source dossier references must be unique")
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("source dossier candidates must be unique")
        return self


def _resolved(value: str) -> ResolutionFieldV1:
    return ResolutionFieldV1(state="resolved", value=value)


def _unresolved(blocker: str) -> ResolutionFieldV1:
    return ResolutionFieldV1(state="unresolved", blocker=blocker)


def _license(component: str, identifier: str, *, resolved: bool) -> ArtifactLicenseV1:
    return ArtifactLicenseV1(
        component=component,
        license_id=(
            _resolved(identifier)
            if resolved
            else _unresolved(f"{component}-license-unverified")
        ),
        redistribution="allowed" if resolved else "unresolved",
        commercial_or_government_use="allowed" if resolved else "unresolved",
        notice_required=True if resolved else None,
    )


def research_references() -> dict[str, ResearchReferenceV1]:
    return {
        key: ResearchReferenceV1(
            reference_id=f"source-{key}",
            url=value["url"],
            title=value["title"],
            publisher=value["publisher"],
            accessed_on=CAPTURED_ON,
            evidence_kind="official_repository",
            supports_claim=value["claim"],
        )
        for key, value in REPOSITORIES.items()
    }


def candidate_manifests() -> dict[str, CandidateArtifactManifestV1]:
    references = research_references()
    manifests: dict[str, CandidateArtifactManifestV1] = {}
    for candidate in CANDIDATES:
        repository = REPOSITORIES.get(candidate.repository_key or "")
        source_reference = (
            references[candidate.repository_key]
            if candidate.repository_key is not None
            else None
        )
        source_revision = (
            _resolved(repository["commit"])
            if repository is not None
            else _unresolved("internal-source-revision-not-created")
        )
        licenses = [_license("code", candidate.code_license, resolved=True)]
        if candidate.role != "stream_local_tracker":
            weights_resolved = candidate.repository_key in {
                "tessdata-fast",
                "tessdata-best",
            }
            licenses.append(
                _license("weights", candidate.code_license, resolved=weights_resolved)
            )
        document = {
            "candidate_id": candidate.candidate_id,
            "semantic_version": "1.0.0",
            "intended_role": candidate.role,
            "source_tier": candidate.source_tier,
            "source_reference": (
                source_reference.model_dump(mode="json") if source_reference else None
            ),
            "source_revision": source_revision.model_dump(mode="json"),
            "artifact_identity": _unresolved(
                candidate.blockers[0]
            ).model_dump(mode="json"),
            "licenses": [license_record.model_dump(mode="json") for license_record in licenses],
            "lineage": _unresolved("training-lineage-unverified").model_dump(mode="json"),
            "model_card": _unresolved("model-card-unresolved").model_dump(mode="json"),
            "sbom": _unresolved("sbom-unresolved").model_dump(mode="json"),
            "supported_taxonomy": list(candidate.supported_taxonomy),
            "runtime_expectations": list(candidate.runtime_expectations),
            "export_expectations": list(candidate.export_expectations),
            "known_limits": list(candidate.known_limits),
            "eligibility": "blocked",
            "blockers": list(candidate.blockers),
            "approval": ApprovalRecordV1(
                record_id=f"pending-{candidate.candidate_id.lower()}",
                owner_id="mayank-admin",
                status="pending",
                reason="Exact artifact remains research-only and unavailable",
            ).model_dump(mode="json"),
            "recorded_at": RECORDED_AT,
        }
        manifests[candidate.candidate_id] = seal_record(
            CandidateArtifactManifestV1,
            document,
        )
    return manifests


def source_research_dossier(
    manifests: dict[str, CandidateArtifactManifestV1] | None = None,
) -> SourceResearchDossierV1:
    values = manifests or candidate_manifests()
    blockers = sorted({blocker for manifest in values.values() for blocker in manifest.blockers})
    return seal_record(
        SourceResearchDossierV1,
        {
            "dossier_id": "p31-model-source-research-v1",
            "captured_at": RECORDED_AT,
            "references": [
                reference.model_dump(mode="json")
                for reference in research_references().values()
            ],
            "candidates": [
                ManifestReferenceV1(
                    record_id=manifest.candidate_id,
                    version=manifest.semantic_version,
                    digest=manifest.manifest_digest,
                ).model_dump(mode="json")
                for manifest in values.values()
            ],
            "downloaded_artifacts": [],
            "unresolved_blockers": blockers,
        },
    )
