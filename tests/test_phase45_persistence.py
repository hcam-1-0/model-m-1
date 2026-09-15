from __future__ import annotations

import pytest

from hcam.intelligence.investigations.canonical import digest, stable_id
from hcam.intelligence.investigations.contracts import (
    CorrectionCommandV1,
    HoldOverlayV1,
)
from hcam.intelligence.investigations.corrections import build_impact_set
from hcam.intelligence.investigations.evidence import register_reference
from hcam.intelligence.investigations.persistence import InvestigationRepository
from hcam.intelligence.investigations.relationships import create_relationship
from hcam.intelligence.investigations.review import record_review


def test_repository_persists_append_only_timeline_evidence_and_jobs(
    p45_app, p45_context: dict
) -> None:
    with p45_app.state.database.session_factory() as session:
        repository = InvestigationRepository(session)
        timeline, reused = repository.create_timeline(p45_context["command"])
        assert reused is False
        duplicate, reused = repository.create_timeline(p45_context["command"])
        assert reused is True
        assert duplicate == timeline

        timeline, reused = repository.append_entry(
            p45_context["entry"](),
            expected_revision=1,
        )
        assert reused is False
        assert timeline.revision == 2
        assert repository.entries(timeline.timeline_id)[0].sequence == 1

        reference = register_reference(
            timeline_id=timeline.timeline_id,
            department=timeline.department,
            source_system_ref=stable_id("ref", "system"),
            source_object_ref=stable_id("ref", "object"),
            source_version="generated.v1",
            content_digest=digest({"evidence": 1}),
            canonicalization_profile="generated.json.v1",
            classification="generated.restricted",
            registered_by=p45_context["actor"],
            reason=p45_context["reason"],
            registered_at=p45_context["now"],
        )
        assert repository.add_evidence(reference)[1] is False
        assert repository.add_evidence(reference)[1] is True

        target = stable_id("ref", "target")
        correction = CorrectionCommandV1(
            correction_id=stable_id("icor", "correction"),
            timeline_id=timeline.timeline_id,
            department=timeline.department,
            kind="retraction",
            target_type="entry",
            target_ref=target,
            target_version=1,
            actor_id=p45_context["actor"],
            reason=p45_context["reason"],
            delivery_id="generated.correction.persistence",
            recorded_at=p45_context["now"],
        )
        impacts = build_impact_set(
            correction,
            {target: [("search", stable_id("ref", "search"))]},
            recorded_at=p45_context["now"],
        )
        repository.add_correction(correction, impacts.impacts)
        job = repository.claim_impact_job("generated.worker", now=p45_context["now"])
        assert job is not None and job.state == "leased"
        repository.complete_impact_job(job, worker_id="generated.worker", now=p45_context["now"])
        assert job.state == "succeeded"
        session.commit()


def test_repository_rejects_revision_and_delivery_collisions(p45_app, p45_context: dict) -> None:
    with p45_app.state.database.session_factory() as session:
        repository = InvestigationRepository(session)
        repository.create_timeline(p45_context["command"])
        entry = p45_context["entry"]()
        repository.append_entry(entry, expected_revision=1)
        conflicting = entry.model_copy(update={"content_digest": digest({"different": True})})
        try:
            repository.append_entry(conflicting, expected_revision=2)
        except ValueError as exc:
            assert "different entry material" in str(exc)
        else:
            raise AssertionError("delivery collision must fail closed")


def test_repository_rejects_correction_identity_collision(p45_app, p45_context: dict) -> None:
    with p45_app.state.database.session_factory() as session:
        repository = InvestigationRepository(session)
        timeline, _ = repository.create_timeline(p45_context["command"])
        target = stable_id("ref", "correction-collision")
        correction = CorrectionCommandV1(
            correction_id=stable_id("icor", "correction-collision"),
            timeline_id=timeline.timeline_id,
            department=timeline.department,
            kind="retraction",
            target_type="entry",
            target_ref=target,
            target_version=1,
            actor_id=p45_context["actor"],
            reason=p45_context["reason"],
            delivery_id="generated.correction.collision",
            recorded_at=p45_context["now"],
        )
        repository.add_correction(correction, [])
        assert repository.add_correction(correction, [])[1] is True
        conflicting = correction.model_copy(update={"target_version": 2})
        try:
            repository.add_correction(conflicting, [])
        except ValueError as exc:
            assert "different command material" in str(exc)
        else:
            raise AssertionError("correction identity collision must fail closed")


def test_repository_enforces_review_chain_and_exact_reuse(p45_app, p45_context: dict) -> None:
    with p45_app.state.database.session_factory() as session:
        repository = InvestigationRepository(session)
        repository.create_timeline(p45_context["command"])
        target = stable_id("ref", "persisted-review")
        first = record_review(
            timeline_id=p45_context["timeline_id"],
            department=p45_context["department"],
            target_ref=target,
            decision="request_information",
            disposition="review_pending",
            revision=1,
            supersedes_review_id=None,
            reviewer_id=p45_context["actor"],
            reason=p45_context["reason"],
            evidence_digest=digest({"review": 1}),
            recorded_at=p45_context["now"],
        )
        assert repository.add_review(first) == (first, False)
        assert repository.add_review(first) == (first, True)
        second = record_review(
            timeline_id=p45_context["timeline_id"],
            department=p45_context["department"],
            target_ref=target,
            decision="no_conclusion",
            disposition="reviewed",
            revision=2,
            supersedes_review_id=first.review_id,
            reviewer_id=p45_context["actor"],
            reason=p45_context["reason"],
            evidence_digest=digest({"review": 2}),
            recorded_at=p45_context["now"],
        )
        assert repository.add_review(second) == (second, False)
        broken = second.model_copy(
            update={
                "review_id": stable_id("irev", "broken-review"),
                "revision": 4,
            }
        )
        with pytest.raises(ValueError, match="contiguous"):
            repository.add_review(broken)


def test_repository_enforces_relationship_and_hold_revision_chains(
    p45_app, p45_context: dict
) -> None:
    with p45_app.state.database.session_factory() as session:
        repository = InvestigationRepository(session)
        source, _ = repository.create_timeline(p45_context["command"])
        target_id = stable_id("inv", "persisted-merge-target")
        target_command = p45_context["command"].model_copy(
            update={
                "timeline_id": target_id,
                "delivery_id": "generated.p45.persisted.target",
            }
        )
        repository.create_timeline(target_command)
        first_relation = create_relationship(
            department=source.department,
            source_timeline_id=source.timeline_id,
            target_timeline_id=target_id,
            kind="merged_into",
            revision=1,
            active=True,
            actor_id=p45_context["actor"],
            reason=p45_context["reason"],
            recorded_at=p45_context["now"],
        )
        assert repository.add_relationship(first_relation) == (first_relation, False)
        assert repository.add_relationship(first_relation) == (first_relation, True)
        assert repository.timeline(source.timeline_id).canonical_timeline_id == target_id
        bad_relation = first_relation.model_copy(
            update={
                "relationship_id": stable_id("irel", "bad-revision"),
                "revision": 3,
                "active": False,
            }
        )
        with pytest.raises(ValueError, match="revision is not next"):
            repository.add_relationship(bad_relation)
        second_relation = first_relation.model_copy(
            update={
                "relationship_id": stable_id("irel", "second-revision"),
                "revision": 2,
                "active": False,
            }
        )
        assert repository.add_relationship(second_relation) == (second_relation, False)
        assert repository.timeline(source.timeline_id).canonical_timeline_id == source.timeline_id

        first_hold = HoldOverlayV1(
            hold_ref=stable_id("ref", "persisted-hold"),
            timeline_id=source.timeline_id,
            department=source.department,
            state="proposed",
            scope_digest=digest({"scope": "persisted"}),
            authority_ref=stable_id("ref", "persisted-authority"),
            revision=1,
            recorded_at=p45_context["now"],
        )
        assert repository.add_hold(first_hold) == first_hold
        assert repository.add_hold(first_hold) == first_hold
        skipped_hold = first_hold.model_copy(
            update={"revision": 3, "state": "simulated_active"}
        )
        with pytest.raises(ValueError, match="revision is not next"):
            repository.add_hold(skipped_hold)
        changed_scope = first_hold.model_copy(
            update={
                "revision": 2,
                "state": "simulated_active",
                "scope_digest": digest({"scope": "changed"}),
            }
        )
        with pytest.raises(ValueError, match="scope cannot change"):
            repository.add_hold(changed_scope)
