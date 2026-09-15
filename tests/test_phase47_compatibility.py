import pytest

from hcam.acceptance.compatibility import (
    build_compatibility_matrix,
    classify_change,
    compatibility_evidence_ref,
    validate_compatibility,
)


def test_compatibility_matrix_and_change_classification() -> None:
    matrix = build_compatibility_matrix(compatibility_evidence_ref())
    validate_compatibility(matrix)
    assert (
        classify_change(
            required_field_added=False,
            authorization_changed=True,
            semantics_changed=False,
        )
        == "security_boundary"
    )
    assert (
        classify_change(
            required_field_added=False,
            authorization_changed=False,
            semantics_changed=True,
        )
        == "breaking_semantic"
    )
    assert (
        classify_change(
            required_field_added=True,
            authorization_changed=False,
            semantics_changed=False,
        )
        == "breaking_schema"
    )
    assert (
        classify_change(
            required_field_added=False,
            authorization_changed=False,
            semantics_changed=False,
        )
        == "optional_additive"
    )


def test_compatibility_rejects_duplicate_or_unmigrated_breaking_change() -> None:
    matrix = build_compatibility_matrix(compatibility_evidence_ref())
    with pytest.raises(ValueError):
        validate_compatibility(
            matrix.model_copy(
                update={"entries": (matrix.entries[0], matrix.entries[0])}
            )
        )
    breaking = matrix.entries[0].model_copy(
        update={"change_class": "breaking_schema", "migration_required": False}
    )
    with pytest.raises(ValueError):
        validate_compatibility(matrix.model_copy(update={"entries": (breaking,)}))
    security = matrix.entries[0].model_copy(
        update={
            "change_class": "security_boundary",
            "migration_required": True,
            "security_review_required": False,
        }
    )
    with pytest.raises(ValueError):
        validate_compatibility(matrix.model_copy(update={"entries": (security,)}))
