from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from hcam.analytics.anpr import (
    AnprBoundaryViolation,
    AnprLocalizationViolation,
    EphemeralGroundTruthCropV1,
    GeneratedPlateFrameV1,
    GroundTruthPlateRegionContentV1,
    PlateLocalizationHypothesisV1,
    PlateLocalizationResultV1,
    SealedGroundTruthPlateRegionV1,
    SyntheticAnprExecutionPolicyV1,
    SyntheticCorpusPlanV1,
    canonical_anpr_evidence_json,
    extract_generated_ground_truth_crop,
    generate_ground_truth_plate_frame,
    generated_ground_truth_fixture,
    localize_generated_ground_truth,
    synthetic_corpus_plan_fixture,
)
from hcam.analytics.anpr.contracts import (
    MAX_ANPR_CROP_HEIGHT,
    MAX_ANPR_CROP_WIDTH,
    MAX_ANPR_FRAME_HEIGHT,
    MAX_ANPR_FRAME_WIDTH,
    MAX_ANPR_PLATE_REGIONS,
)


def _enabled_policy() -> SyntheticAnprExecutionPolicyV1:
    return SyntheticAnprExecutionPolicyV1(enabled=True, environment="test")


def _fixture() -> tuple[
    GeneratedPlateFrameV1,
    PlateLocalizationResultV1,
    EphemeralGroundTruthCropV1,
]:
    return generated_ground_truth_fixture(
        synthetic_corpus_plan_fixture(),
        policy=_enabled_policy(),
    )


def test_ground_truth_frame_localization_and_crop_replay_exactly_twenty_times() -> None:
    plan = synthetic_corpus_plan_fixture()
    policy = _enabled_policy()
    expected = generated_ground_truth_fixture(plan, policy=policy)

    for _ in range(20):
        assert generated_ground_truth_fixture(plan, policy=policy) == expected


def test_plan_seed_change_changes_frame_and_crop_digests() -> None:
    first_plan = synthetic_corpus_plan_fixture()
    changed = first_plan.model_dump(mode="json")
    changed["root_seed"] += 1
    changed["plan_id"] = "anprplan_44444444444444444444444444444444"
    second_plan = SyntheticCorpusPlanV1.model_validate(changed)
    policy = _enabled_policy()

    first = generated_ground_truth_fixture(first_plan, policy=policy)
    second = generated_ground_truth_fixture(second_plan, policy=policy)

    assert first[0].frame_digest != second[0].frame_digest
    assert first[2].descriptor.crop_digest != second[2].descriptor.crop_digest


@pytest.mark.parametrize(
    ("sample_index", "expected_layout", "expected_size"),
    [(0, "single_line", (240, 64)), (1, "two_line", (168, 96))],
)
def test_both_layouts_have_bounded_generated_ground_truth_geometry(
    sample_index: int,
    expected_layout: str,
    expected_size: tuple[int, int],
) -> None:
    frame = generate_ground_truth_plate_frame(
        synthetic_corpus_plan_fixture(),
        "contract_fixture",
        sample_index,
        policy=_enabled_policy(),
    )
    crop = extract_generated_ground_truth_crop(frame)

    assert frame.request.layout == expected_layout
    assert frame.ground_truth_region.content.layout == expected_layout
    assert (crop.descriptor.width, crop.descriptor.height) == expected_size
    assert frame.width <= MAX_ANPR_FRAME_WIDTH
    assert frame.height <= MAX_ANPR_FRAME_HEIGHT
    assert crop.descriptor.width <= MAX_ANPR_CROP_WIDTH
    assert crop.descriptor.height <= MAX_ANPR_CROP_HEIGHT


def test_crop_pixels_are_the_exact_axis_aligned_source_slice() -> None:
    frame, _, crop = _fixture()
    bbox = frame.ground_truth_region.content.bbox
    left = round(bbox.x * frame.width)
    top = round(bbox.y * frame.height)
    right = round((bbox.x + bbox.width) * frame.width)
    bottom = round((bbox.y + bbox.height) * frame.height)
    stride = frame.width * 3
    expected = b"".join(
        frame.bgr_bytes[row * stride + left * 3 : row * stride + right * 3]
        for row in range(top, bottom)
    )

    assert crop.bgr_bytes == expected
    assert crop.descriptor.transform_matrix == (
        1.0,
        0.0,
        float(-left),
        0.0,
        1.0,
        float(-top),
        0.0,
        0.0,
        1.0,
    )


def test_localization_is_ground_truth_only_and_has_no_model_or_text_surface() -> None:
    frame, localization, crop = _fixture()

    assert localization.source_frame_digest == frame.frame_digest
    assert localization.hypothesis_count == 1
    assert len(localization.hypotheses) == 1
    assert localization.candidate_id is None
    assert localization.model_execution_performed is False
    assert localization.weights_loaded is False
    assert localization.crop_bytes_returned is False
    assert localization.image_path_returned is False
    assert localization.media_url_returned is False
    assert localization.plate_text_returned is False
    assert crop.descriptor.model_execution_performed is False
    assert crop.descriptor.pixels_ephemeral is True
    assert crop.descriptor.pixels_persisted is False
    assert MAX_ANPR_PLATE_REGIONS == 8


def test_canonical_evidence_rejects_ephemeral_frame_and_crop_objects() -> None:
    frame, _, crop = _fixture()

    with pytest.raises(AnprBoundaryViolation) as frame_error:
        canonical_anpr_evidence_json(frame)  # type: ignore[arg-type]
    assert frame_error.value.code == "non_json_input"

    with pytest.raises(AnprBoundaryViolation) as crop_error:
        canonical_anpr_evidence_json(crop)  # type: ignore[arg-type]
    assert crop_error.value.code == "non_json_input"


def test_sanitized_evidence_has_no_pixels_paths_urls_or_plate_text() -> None:
    _, localization, crop = _fixture()
    document = canonical_anpr_evidence_json(
        {
            "localization": localization.model_dump(mode="json"),
            "crop": crop.descriptor.model_dump(mode="json"),
        },
        maximum_bytes=32 * 1024,
        maximum_nodes=1_024,
    )

    assert '"bgr_bytes"' not in document
    assert '"bytes"' not in document
    assert '"path"' not in document
    assert '"url"' not in document
    assert '"media"' not in document
    assert '"token"' not in document
    assert "SYN-" not in document


def test_generation_is_default_off_and_production_forbidden() -> None:
    plan = synthetic_corpus_plan_fixture()
    with pytest.raises(AnprBoundaryViolation) as disabled:
        generate_ground_truth_plate_frame(
            plan,
            "contract_fixture",
            0,
            policy=SyntheticAnprExecutionPolicyV1(),
        )
    assert disabled.value.code == "runtime_disabled"

    with pytest.raises(ValidationError, match="forbidden in production"):
        SyntheticAnprExecutionPolicyV1(enabled=True, environment="production")


def test_malformed_frame_bytes_and_lineage_fail_with_bounded_codes() -> None:
    frame, _, _ = _fixture()
    with pytest.raises(AnprLocalizationViolation) as byte_count:
        GeneratedPlateFrameV1(
            width=frame.width,
            height=frame.height,
            bgr_bytes=frame.bgr_bytes[:-1],
            request=frame.request,
            ground_truth_region=frame.ground_truth_region,
        )
    assert byte_count.value.code == "frame_byte_count_mismatch"

    with pytest.raises(AnprLocalizationViolation) as lineage:
        GeneratedPlateFrameV1(
            width=frame.width,
            height=frame.height,
            bgr_bytes=frame.bgr_bytes,
            request=frame.request,
            ground_truth_region=frame.ground_truth_region,
            source_id="unapproved-source",
        )
    assert lineage.value.code == "generated_lineage_mismatch"


def test_region_digest_and_quadrilateral_tampering_are_rejected() -> None:
    frame, localization, _ = _fixture()
    region_document = frame.ground_truth_region.model_dump(mode="json")
    region_document["region_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ValidationError, match="digest does not match"):
        SealedGroundTruthPlateRegionV1.model_validate(region_document)

    content_document = frame.ground_truth_region.content.model_dump(mode="json")
    content_document["quadrilateral"][0]["x"] += 0.01
    with pytest.raises(ValidationError, match="quadrilateral"):
        GroundTruthPlateRegionContentV1.model_validate(content_document)

    hypothesis_document = localization.hypotheses[0].model_dump(mode="json")
    hypothesis_document["quadrilateral"][1]["y"] += 0.01
    with pytest.raises(ValidationError, match="quadrilateral"):
        PlateLocalizationHypothesisV1.model_validate(hypothesis_document)


def test_crop_descriptor_digest_is_bound_to_ephemeral_pixels() -> None:
    _, _, crop = _fixture()
    with pytest.raises(AnprLocalizationViolation) as changed:
        EphemeralGroundTruthCropV1(
            descriptor=crop.descriptor,
            bgr_bytes=bytes([crop.bgr_bytes[0] ^ 1]) + crop.bgr_bytes[1:],
        )
    assert changed.value.code == "crop_digest_mismatch"


def test_frames_crops_and_contracts_are_immutable() -> None:
    frame, localization, crop = _fixture()

    with pytest.raises(FrozenInstanceError):
        frame.width = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        crop.bgr_bytes = b""  # type: ignore[misc]
    with pytest.raises(ValidationError):
        changed = copy.copy(localization)
        changed.hypothesis_count = 0


def test_generation_uses_no_file_or_network_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import socket

    plan = synthetic_corpus_plan_fixture()
    policy = _enabled_policy()

    def deny(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("W4 attempted an external input operation")

    monkeypatch.setattr(builtins, "open", deny)
    monkeypatch.setattr(socket, "create_connection", deny)

    frame = generate_ground_truth_plate_frame(
        plan,
        "contract_fixture",
        0,
        policy=policy,
    )
    assert localize_generated_ground_truth(frame).hypothesis_count == 1
    assert (
        extract_generated_ground_truth_crop(frame).descriptor.pixels_persisted is False
    )
