from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from hcam.intelligence.alerts.adapters import (
    DisabledWorkflowAdapter,
    GeneratedLabEvaluationIngressAdapter,
    GeneratedWorkflowExecutor,
)
from hcam.intelligence.alerts.authority import authorize_action
from hcam.intelligence.alerts.budgets import BudgetObservation, evaluate_budget
from hcam.intelligence.alerts.canonical import stable_id
from hcam.intelligence.alerts.contracts import (
    AlertAggregateV2,
    AlertBudgetPolicyV1,
    AlertLifecycleCommandV1,
    AlertReviewDecisionV1,
    AlertTimerIntentV1,
    LabEvaluationIngressV1,
    ProposedAlertCommandV1,
    ReviewQuorumPolicyV1,
    SystemHealthActionV1,
    WorkflowExecutionRequestV1,
)
from hcam.intelligence.alerts.identity import derive_alert_identity
from hcam.intelligence.alerts.lifecycle import TRANSITIONS, apply_transition
from hcam.intelligence.alerts.review import ReviewQuorum
from hcam.intelligence.alerts.timers import claim_timer, complete_timer


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "contracts" / "phase-4" / "p4-3" / "fixtures"
SCHEMAS = {
    "generated-alert-proposals-v1.json": "hcam.p4-3.generated-alert-proposals.v1",
    "generated-lifecycle-cases-v1.json": "hcam.p4-3.generated-lifecycle-cases.v1",
    "generated-quorum-cases-v1.json": "hcam.p4-3.generated-quorum-cases.v1",
    "generated-budget-cases-v1.json": "hcam.p4-3.generated-budget-cases.v1",
    "generated-timer-cases-v1.json": "hcam.p4-3.generated-timer-cases.v1",
    "generated-workflow-adapter-cases-v1.json": "hcam.p4-3.generated-workflow-adapter-cases.v1",
    "generated-lab-ingress-cases-v1.json": "hcam.p4-3.generated-lab-ingress-cases.v1",
    "generated-system-health-cases-v1.json": "hcam.p4-3.generated-system-health-cases.v1",
}
BASE = datetime(2026, 1, 1, tzinfo=UTC)
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


def _proposal(index: int, *, system_health: bool = False) -> dict[str, Any]:
    suffix = f"{index:032x}"
    return {
        "contract_type": "hcam.p4-3.proposed-alert-command.v1",
        "delivery_id": f"generated.delivery.{index}",
        "evaluation_id": f"revl_{suffix}",
        "evaluation_revision": 1,
        "evaluation_digest": DIGEST_A,
        "rule_record_id": f"irlr_{suffix}",
        "compilation_id": f"rcmp_{suffix}",
        "department": "generated-lab",
        "partition_digest": DIGEST_B,
        "domain": "system_health" if system_health else "police_intelligence",
        "authority_class": "bounded_automation" if system_health else "mandatory_review",
        "occurred_at": (BASE + timedelta(seconds=index)).isoformat(),
        "evidence_refs": [f"generated.evidence.{index}"],
        "incident_key": f"generated.incident.{index % 4}",
        "severity": ("information", "low", "medium", "high", "critical")[index % 5],
        "priority": ("routine", "standard", "urgent", "immediate")[index % 4],
        "confidence": round(0.5 + (index % 5) * 0.1, 2),
        "certainty": round(0.4 + (index % 5) * 0.1, 2),
        "chronology_confidence": 0.9,
        "generated_only": True,
        "operational": False,
    }


def build_fixtures() -> dict[str, dict[str, Any]]:
    proposals = [_proposal(index, system_health=index >= 12) for index in range(16)]
    lifecycle = [
        {"from": source, "action": action, "to": target}
        for source, actions in TRANSITIONS.items()
        for action, target in actions.items()
    ]
    return {
        "generated-alert-proposals-v1.json": {
            "schema_version": SCHEMAS["generated-alert-proposals-v1.json"],
            "generated_only": True,
            "proposals": proposals,
        },
        "generated-lifecycle-cases-v1.json": {
            "schema_version": SCHEMAS["generated-lifecycle-cases-v1.json"],
            "generated_only": True,
            "cases": lifecycle,
        },
        "generated-quorum-cases-v1.json": {
            "schema_version": SCHEMAS["generated-quorum-cases-v1.json"],
            "generated_only": True,
            "cases": [
                {"required": 1, "votes": ["approve"], "expected": "approved"},
                {"required": 1, "votes": ["deny"], "expected": "rejected"},
                {"required": 2, "votes": ["approve"], "expected": "pending"},
                {"required": 2, "votes": ["approve", "approve"], "expected": "approved"},
                {"required": 2, "votes": ["deny", "deny"], "expected": "rejected"},
                {"required": 2, "votes": ["approve", "deny"], "expected": "disagreement"},
            ],
        },
        "generated-budget-cases-v1.json": {
            "schema_version": SCHEMAS["generated-budget-cases-v1.json"],
            "generated_only": True,
            "cases": [
                {"count": 0, "limit": 2, "admitted": True},
                {"count": 1, "limit": 2, "admitted": True},
                {"count": 2, "limit": 2, "admitted": False},
                {"count": 9, "limit": 2, "admitted": False},
            ],
        },
        "generated-timer-cases-v1.json": {
            "schema_version": SCHEMAS["generated-timer-cases-v1.json"],
            "generated_only": True,
            "cases": [
                {"attempts": 0, "alert_version": 1, "expected": "completed"},
                {"attempts": 1, "alert_version": 2, "expected": "cancelled"},
            ],
        },
        "generated-workflow-adapter-cases-v1.json": {
            "schema_version": SCHEMAS["generated-workflow-adapter-cases-v1.json"],
            "generated_only": True,
            "cases": [
                {"adapter": "local_bounded", "expected": "applied"},
                {"adapter": "generated_simulator", "expected": "applied"},
                {"adapter": "future_disabled", "expected": "adapter_disabled"},
            ],
        },
        "generated-lab-ingress-cases-v1.json": {
            "schema_version": SCHEMAS["generated-lab-ingress-cases-v1.json"],
            "generated_only": True,
            "cases": [
                {
                    "fixture_id": f"generated.lab.{index}",
                    "adapter_profile": "lab1highadapter" if index % 2 else "lab2lowadapter",
                    "camera_slot": index,
                    "media_profile": ("low", "medium", "high")[index % 3],
                    "availability": ("available", "degraded", "offline")[index % 3],
                    "sample_epoch": index,
                    "metadata_digest": DIGEST_A,
                    "generated_only": True,
                    "sanitized": True,
                    "network_locator": None,
                    "credential_ref": None,
                    "media_payload": None,
                }
                for index in range(1, 51)
            ],
        },
        "generated-system-health-cases-v1.json": {
            "schema_version": SCHEMAS["generated-system-health-cases-v1.json"],
            "generated_only": True,
            "actions": ["route", "suppress_duplicate", "resolve_synthetic_health"],
            "denied_police_actions": ["accept", "reject", "dispatch", "enforce"],
        },
    }


def _encoded(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def write_fixtures() -> None:
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    for name, value in build_fixtures().items():
        (FIXTURE_ROOT / name).write_bytes(_encoded(value))


def validate_fixtures() -> dict[str, int]:
    expected = build_fixtures()
    for name, value in expected.items():
        path = FIXTURE_ROOT / name
        if path.read_bytes() != _encoded(value):
            raise ValueError(f"generated fixture drift: {name}")
    proposal_values = expected["generated-alert-proposals-v1.json"]["proposals"]
    proposals = [ProposedAlertCommandV1.model_validate(item) for item in proposal_values]
    if any(derive_alert_identity(item) != derive_alert_identity(item) for item in proposals):
        raise ValueError("alert identity is not deterministic")

    base_proposal = proposals[0]
    aggregate = AlertAggregateV2(
        alert_id=derive_alert_identity(base_proposal).alert_id,
        version=1,
        department=base_proposal.department,
        semantic_key=derive_alert_identity(base_proposal).semantic_key,
        delivery_key=derive_alert_identity(base_proposal).delivery_key,
        source_evaluation_id=base_proposal.evaluation_id,
        source_evaluation_revision=1,
        source_evaluation_digest=base_proposal.evaluation_digest,
        incident_key=base_proposal.incident_key,
        state="proposed",
        domain="police_intelligence",
        authority_class="mandatory_review",
        severity=base_proposal.severity,
        priority=base_proposal.priority,
        confidence=base_proposal.confidence,
        certainty=base_proposal.certainty,
        chronology_confidence=base_proposal.chronology_confidence,
        disposition="unreviewed",
        evidence_refs=base_proposal.evidence_refs,
        policy_digest=DIGEST_A,
        created_at=BASE,
        updated_at=BASE,
    )
    for index, case in enumerate(expected["generated-lifecycle-cases-v1.json"]["cases"]):
        current = aggregate.model_copy(update={"state": case["from"], "version": index + 1})
        if case["from"] == "merged":
            current = current.model_copy(update={"merged_into": aggregate.alert_id})
        if case["from"] == "suppressed":
            current = current.model_copy(update={"suppression_code": "generated_suppression"})
        command = AlertLifecycleCommandV1(
            command_id=f"generated.command.{index}",
            action=case["action"],
            expected_version=current.version,
            actor_id="generated-reviewer",
            reason="Generated lifecycle fixture",
            target_alert_id=("alt_" + "f" * 32) if case["action"] == "merge" else None,
        )
        updated, _ = apply_transition(current, command, now=BASE + timedelta(seconds=index + 1))
        if updated.state != case["to"]:
            raise ValueError("generated lifecycle case does not match")

    quorum_cases = expected["generated-quorum-cases-v1.json"]["cases"]
    for case_index, case in enumerate(quorum_cases):
        policy = ReviewQuorumPolicyV1(
            policy_id=f"generated.quorum.{case_index}",
            policy_version=1,
            department="generated-lab",
            workflow_class="ordinary" if case["required"] == 1 else "generated_high_impact",
            required_distinct_reviewers=case["required"],
            permitted_roles=["intelligence.reviewer"],
            evidence_digest=DIGEST_A,
            effective_at=BASE,
        )
        quorum = ReviewQuorum(policy)
        for vote_index, vote in enumerate(case["votes"]):
            quorum.add(
                AlertReviewDecisionV1(
                    decision_id=stable_id("ardc", case_index, vote_index),
                    alert_id=aggregate.alert_id,
                    department="generated-lab",
                    policy_id=policy.policy_id,
                    policy_version=1,
                    reviewer_id=f"generated-reviewer-{vote_index}",
                    reviewer_role="intelligence.reviewer",
                    decision=vote,
                    evidence_digest=DIGEST_A,
                    reason="Generated review fixture",
                    recorded_at=BASE,
                ),
                now=BASE,
            )
        if quorum.outcome != case["expected"]:
            raise ValueError("generated quorum case does not match")

    budget_cases = expected["generated-budget-cases-v1.json"]["cases"]
    for index, case in enumerate(budget_cases):
        policy = AlertBudgetPolicyV1(
            policy_id=f"generated.budget.{index}",
            version=1,
            department="generated-lab",
            limits=[{"scope": "department", "scope_key": "generated-lab", "window_seconds": 60, "limit": case["limit"]}],
            policy_digest=DIGEST_A,
        )
        result = evaluate_budget(
            base_proposal,
            policy,
            [BudgetObservation("department", "generated-lab", BASE, case["count"])],
        )
        if result.admitted is not case["admitted"]:
            raise ValueError("generated budget case does not match")

    timer_cases = expected["generated-timer-cases-v1.json"]["cases"]
    for index, case in enumerate(timer_cases):
        timer = AlertTimerIntentV1(
            timer_id=stable_id("atmr", index),
            alert_id=aggregate.alert_id,
            department="generated-lab",
            timer_kind="review_sla",
            due_at=BASE,
            state="pending",
            attempt_count=case["attempts"],
            expected_alert_version=1,
            payload_digest=DIGEST_A,
        )
        claimed = claim_timer(timer, worker_id="generated-worker", now=BASE)
        result = complete_timer(claimed, worker_id="generated-worker", alert_version=case["alert_version"])
        if result.state != case["expected"]:
            raise ValueError("generated timer case does not match")

    workflow_cases = expected["generated-workflow-adapter-cases-v1.json"]["cases"]
    for index, case in enumerate(workflow_cases):
        timer = AlertTimerIntentV1(
            timer_id=stable_id("atmr", "workflow", index),
            alert_id=aggregate.alert_id,
            department="generated-lab",
            timer_kind="review_sla",
            due_at=BASE,
            state="leased",
            attempt_count=1,
            lease_owner="generated-worker",
            lease_until=BASE + timedelta(seconds=90),
            expected_alert_version=1,
            payload_digest=DIGEST_A,
        )
        request = WorkflowExecutionRequestV1(
            execution_id=stable_id("awfx", index), timer=timer, adapter_kind=case["adapter"]
        )
        adapter = DisabledWorkflowAdapter() if case["adapter"] == "future_disabled" else GeneratedWorkflowExecutor()
        if adapter.execute(request).outcome != case["expected"]:
            raise ValueError("generated workflow adapter case does not match")

    lab_cases = expected["generated-lab-ingress-cases-v1.json"]["cases"]
    adapter = GeneratedLabEvaluationIngressAdapter()
    for value in lab_cases:
        item = LabEvaluationIngressV1.model_validate(value)
        if adapter.normalize(item) != item:
            raise ValueError("generated lab ingress case does not match")

    for action in expected["generated-system-health-cases-v1.json"]["actions"]:
        health = proposals[-1]
        authorize_action(health, action)
        SystemHealthActionV1(
            alert_id=derive_alert_identity(health).alert_id,
            action=action,
            policy_digest=DIGEST_A,
        )
    return {
        "fixtures": len(expected),
        "proposals": len(proposals),
        "lifecycle_cases": len(expected["generated-lifecycle-cases-v1.json"]["cases"]),
        "quorum_cases": len(quorum_cases),
        "budget_cases": len(budget_cases),
        "timer_cases": len(timer_cases),
        "workflow_cases": len(workflow_cases),
        "lab_cases": len(lab_cases),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or validate P4.3 generated-only alert fixtures")
    parser.add_argument("command", choices=("generate", "check"))
    arguments = parser.parse_args()
    try:
        if arguments.command == "generate":
            write_fixtures()
        summary = validate_fixtures()
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"passed": False, "failure_code": "generated_alert_fixture_validation_failed", "detail": type(exc).__name__}, separators=(",", ":"), sort_keys=True))
        return 1
    print(json.dumps({"passed": True, "generated_only": True, **summary}, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
