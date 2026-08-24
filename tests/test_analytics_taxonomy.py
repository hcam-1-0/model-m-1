from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hcam.analytics.contracts import canonical_contract_json
from hcam.analytics.taxonomy import TaxonomyManifestV1


FIXTURE = (
    Path(__file__).parents[1]
    / "contracts"
    / "phase-3"
    / "fixtures"
    / "taxonomy-draft-v1.json"
)


def _document() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_draft_taxonomy_fixture_is_deterministic_and_not_approved() -> None:
    taxonomy = TaxonomyManifestV1.model_validate(_document())

    assert taxonomy.status == "draft"
    assert taxonomy.approval_record_id is None
    assert taxonomy.independent_reviewer_id is None
    assert canonical_contract_json(taxonomy) == FIXTURE.read_text(encoding="utf-8")


def test_taxonomy_class_ids_must_be_unique() -> None:
    document = _document()
    classes = document["classes"]
    assert isinstance(classes, list)
    classes.append(copy.deepcopy(classes[0]))

    with pytest.raises(ValidationError, match="class IDs must be unique"):
        TaxonomyManifestV1.model_validate(document)


def test_taxonomy_parent_must_exist() -> None:
    document = _document()
    classes = document["classes"]
    assert isinstance(classes, list) and isinstance(classes[1], dict)
    classes[1]["parent_id"] = "object.missing"

    with pytest.raises(ValidationError, match="parent_id must reference"):
        TaxonomyManifestV1.model_validate(document)


def test_taxonomy_hierarchy_must_not_cycle() -> None:
    document = _document()
    classes = document["classes"]
    assert isinstance(classes, list) and isinstance(classes[0], dict)
    classes[0]["parent_id"] = "object.person"

    with pytest.raises(ValidationError, match="must not contain a cycle"):
        TaxonomyManifestV1.model_validate(document)


@pytest.mark.parametrize(
    "class_id,display_name",
    [
        ("person.face", "Face"),
        ("person.identity", "Identifier"),
        ("person.emotion", "Expression"),
        ("person.risk", "Risk"),
        ("person.reid", "Cross camera descriptor"),
        ("person.profile", "Profile",),
    ],
)
def test_prohibited_attribute_taxonomy_is_rejected(
    class_id: str,
    display_name: str,
) -> None:
    document = _document()
    classes = document["classes"]
    assert isinstance(classes, list) and isinstance(classes[1], dict)
    classes[1]["id"] = class_id
    classes[1]["display_name"] = display_name

    with pytest.raises(ValidationError, match="prohibited attribute category"):
        TaxonomyManifestV1.model_validate(document)


def test_taxonomy_must_keep_all_non_negotiable_prohibited_uses() -> None:
    document = _document()
    uses = document["prohibited_uses"]
    assert isinstance(uses, list)
    uses.pop()

    with pytest.raises(ValidationError):
        TaxonomyManifestV1.model_validate(document)


def test_taxonomy_intended_use_cannot_open_a_prohibited_purpose() -> None:
    document = _document()
    document["intended_use"] = "Predictive individual risk classification"

    with pytest.raises(ValidationError, match="prohibited analytics purpose"):
        TaxonomyManifestV1.model_validate(document)


def test_approved_taxonomy_requires_owner_approval_record() -> None:
    document = _document()
    document["status"] = "approved"

    with pytest.raises(ValidationError, match="requires approval record"):
        TaxonomyManifestV1.model_validate(document)

    document["approval_record_id"] = "DR-TAXONOMY-001"
    approved = TaxonomyManifestV1.model_validate(document)
    assert approved.status == "approved"
    assert approved.independent_reviewer_id is None

    document["independent_reviewer_id"] = "phase3-owner"
    owner_reviewed = TaxonomyManifestV1.model_validate(document)
    assert owner_reviewed.independent_reviewer_id == owner_reviewed.owner_id
