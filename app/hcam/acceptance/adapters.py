from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from hcam.acceptance.canonical import digest
from hcam.acceptance.contracts import AdapterResponseV1, ScenarioStepV1
from hcam.acceptance.determinism import IdentifierProvider


class ApplicationBoundary(Protocol):
    """Narrow command boundary used by the generated acceptance engine."""

    def execute(
        self,
        step: ScenarioStepV1,
        *,
        logical_at: datetime,
        identifiers: IdentifierProvider,
    ) -> AdapterResponseV1: ...

    def snapshot(self) -> Mapping[str, Any]: ...

    def terminal_state(self) -> str: ...


class AdapterBoundaryError(RuntimeError):
    reason_code = "adapter.boundary_denied"


@dataclass(slots=True)
class GeneratedApplicationBoundary:
    """Generated state machine that exposes service commands, never persistence."""

    scenario_id: str
    events: dict[str, dict[str, Any]] = field(default_factory=dict)
    hypotheses: dict[str, dict[str, Any]] = field(default_factory=dict)
    alerts: dict[str, dict[str, Any]] = field(default_factory=dict)
    investigations: dict[str, dict[str, Any]] = field(default_factory=dict)
    evidence_references: dict[str, dict[str, Any]] = field(default_factory=dict)
    signals: list[dict[str, Any]] = field(default_factory=list)
    corrections: list[dict[str, Any]] = field(default_factory=list)
    conflict_recorded: bool = False
    cross_scope_denied: bool = False
    reference_state: str = "not_queried"
    worker_state: str = "active"
    rule_state: str = "not_evaluated"
    reviewed: bool = False
    review_state: str = "not_reviewed"
    _mutation_count: int = 0

    def _response(
        self,
        step: ScenarioStepV1,
        *,
        outcome: str,
        reason: str,
        state: str,
        output: dict[str, Any] | None = None,
        mutated: bool = False,
    ) -> AdapterResponseV1:
        if mutated:
            self._mutation_count += 1
        return AdapterResponseV1(
            action=step.action,
            outcome=outcome,
            reason_code=reason,
            state=state,
            output=output or {"generated_marker": self.scenario_id.lower()},
            mutation_count=1 if mutated else 0,
        )

    def execute(
        self,
        step: ScenarioStepV1,
        *,
        logical_at: datetime,
        identifiers: IdentifierProvider,
    ) -> AdapterResponseV1:
        handler = getattr(self, f"_action_{step.action}", None)
        if handler is None:
            raise AdapterBoundaryError("scenario action is not allowlisted")
        return handler(step, logical_at=logical_at, identifiers=identifiers)

    def _action_observe_event(self, step, *, logical_at, identifiers):
        event_ref = identifiers.issue(self.scenario_id, "event", prefix="ref")
        self.events[event_ref] = {
            "event_ref": event_ref,
            "event_kind": step.input_data["event_kind"],
            "logical_at": logical_at.isoformat(),
            "content_digest": digest(step.input_data),
            "generated_only": True,
        }
        return self._response(
            step,
            outcome="accepted",
            reason="event.observed",
            state="event_observed",
            output={"event_ref": event_ref, "generated_only": True},
            mutated=True,
        )

    def _action_duplicate_event(self, step, *, logical_at, identifiers):
        del logical_at, identifiers
        if not self.events:
            return self._response(
                step, outcome="denied", reason="event.source_missing", state="denied"
            )
        event_ref = next(iter(self.events))
        return self._response(
            step,
            outcome="duplicate",
            reason="event.duplicate_suppressed",
            state="duplicate_suppressed",
            output={"event_ref": event_ref, "reused": True},
        )

    def _action_record_late_conflict(self, step, *, logical_at, identifiers):
        conflict_ref = identifiers.issue(self.scenario_id, "conflict", prefix="ref")
        self.conflict_recorded = True
        return self._response(
            step,
            outcome="degraded",
            reason="chronology.conflict_recorded",
            state="conflict_recorded",
            output={"conflict_ref": conflict_ref, "logical_at": logical_at.isoformat()},
            mutated=True,
        )

    def _action_correlate(self, step, *, logical_at, identifiers):
        if not self.events:
            return self._response(
                step,
                outcome="denied",
                reason="correlation.source_missing",
                state="denied",
            )
        if step.input_data.get("no_match"):
            return self._response(
                step,
                outcome="abstained",
                reason="correlation.no_match",
                state="abstained",
            )
        if self.conflict_recorded:
            return self._response(
                step,
                outcome="abstained",
                reason="correlation.conflict_abstained",
                state="conflict_recorded",
            )
        hypothesis_ref = identifiers.issue(self.scenario_id, "hypothesis", prefix="ref")
        self.hypotheses[hypothesis_ref] = {
            "hypothesis_ref": hypothesis_ref,
            "source_refs": sorted(self.events),
            "logical_at": logical_at.isoformat(),
            "authoritative": False,
            "generated_only": True,
        }
        return self._response(
            step,
            outcome="accepted",
            reason="correlation.hypothesis_created",
            state="hypothesis_created",
            output={"hypothesis_ref": hypothesis_ref, "authoritative": False},
            mutated=True,
        )

    def _action_evaluate_rule(self, step, *, logical_at, identifiers):
        del logical_at, identifiers
        if not self.hypotheses:
            self.rule_state = "not_matched"
            return self._response(
                step, outcome="abstained", reason="rule.not_matched", state="abstained"
            )
        self.rule_state = "matched"
        return self._response(
            step,
            outcome="accepted",
            reason="rule.matched",
            state="rule_matched",
            output={"matched": True, "grants_authority": False},
            mutated=True,
        )

    def _action_propose_alert(self, step, *, logical_at, identifiers):
        if self.rule_state != "matched":
            return self._response(
                step, outcome="denied", reason="alert.rule_not_matched", state="denied"
            )
        alert_ref = identifiers.issue(self.scenario_id, "alert", prefix="ref")
        self.alerts[alert_ref] = {
            "alert_ref": alert_ref,
            "state": "proposed",
            "logical_at": logical_at.isoformat(),
            "mandatory_review": True,
            "generated_only": True,
        }
        return self._response(
            step,
            outcome="accepted",
            reason="alert.proposed",
            state="alert_proposed",
            output={"alert_ref": alert_ref, "mandatory_review": True},
            mutated=True,
        )

    def _action_query_reference(self, step, *, logical_at, identifiers):
        del logical_at
        mode = step.input_data.get("reference_mode", "candidate")
        if mode == "abstain":
            self.reference_state = "abstained"
            return self._response(
                step,
                outcome="abstained",
                reason="reference.abstained",
                state="abstained",
            )
        if mode == "unavailable":
            self.reference_state = "unavailable"
            return self._response(
                step,
                outcome="degraded",
                reason="reference.unavailable",
                state="reference_degraded",
            )
        candidate_ref = identifiers.issue(self.scenario_id, "candidate", prefix="ref")
        self.reference_state = "candidate_set"
        return self._response(
            step,
            outcome="accepted",
            reason="reference.candidate_set_created",
            state="candidate_set_created",
            output={"candidate_ref": candidate_ref, "identity_confirmed": False},
            mutated=True,
        )

    def _action_review_alert(self, step, *, logical_at, identifiers):
        del logical_at, identifiers
        if not self.alerts:
            return self._response(
                step, outcome="denied", reason="review.alert_missing", state="denied"
            )
        self.reviewed = True
        decision = step.input_data.get("decision")
        alert = next(iter(self.alerts.values()))
        if decision == "deny":
            self.review_state = "denied"
            alert["state"] = "rejected"
            return self._response(
                step,
                outcome="denied",
                reason="review.denied",
                state="review_denied",
                mutated=True,
            )
        self.review_state = "approved"
        alert["state"] = "accepted"
        return self._response(
            step,
            outcome="accepted",
            reason="review.approved",
            state="accepted",
            mutated=True,
        )

    def _action_transition_alert(self, step, *, logical_at, identifiers):
        del logical_at, identifiers
        if not self.alerts or self.review_state != "approved":
            return self._response(
                step,
                outcome="denied",
                reason="alert.transition_denied",
                state="review_denied",
            )
        alert = next(iter(self.alerts.values()))
        alert["state"] = step.input_data["target_state"]
        return self._response(
            step,
            outcome="accepted",
            reason="alert.closed",
            state="alert_closed",
            mutated=True,
        )

    def _action_open_investigation(self, step, *, logical_at, identifiers):
        if not self.alerts or next(iter(self.alerts.values()))["state"] not in {
            "accepted",
            "closed",
        }:
            return self._response(
                step,
                outcome="denied",
                reason="investigation.alert_not_accepted",
                state="denied",
            )
        investigation_ref = identifiers.issue(
            self.scenario_id, "investigation", prefix="ref"
        )
        self.investigations[investigation_ref] = {
            "investigation_ref": investigation_ref,
            "logical_at": logical_at.isoformat(),
            "entries": [],
            "generated_only": True,
        }
        return self._response(
            step,
            outcome="accepted",
            reason="investigation.opened",
            state="investigation_opened",
            output={"investigation_ref": investigation_ref},
            mutated=True,
        )

    def _action_append_evidence_reference(self, step, *, logical_at, identifiers):
        if not self.investigations:
            return self._response(
                step,
                outcome="denied",
                reason="evidence.investigation_missing",
                state="denied",
            )
        evidence_ref = identifiers.issue(self.scenario_id, "evidence", prefix="ref")
        self.evidence_references[evidence_ref] = {
            "evidence_ref": evidence_ref,
            "logical_at": logical_at.isoformat(),
            "content_copied": False,
            "generated_only": True,
        }
        return self._response(
            step,
            outcome="accepted",
            reason="evidence.reference_registered",
            state="evidence_registered",
            output={"evidence_ref": evidence_ref, "content_copied": False},
            mutated=True,
        )

    def _action_record_correction(self, step, *, logical_at, identifiers):
        correction_ref = identifiers.issue(self.scenario_id, "correction", prefix="ref")
        self.corrections.append(
            {
                "ref": correction_ref,
                "kind": "correction",
                "logical_at": logical_at.isoformat(),
            }
        )
        return self._response(
            step,
            outcome="accepted",
            reason="correction.recorded",
            state="corrected",
            output={"correction_ref": correction_ref},
            mutated=True,
        )

    def _action_record_retraction(self, step, *, logical_at, identifiers):
        retraction_ref = identifiers.issue(self.scenario_id, "retraction", prefix="ref")
        self.corrections.append(
            {
                "ref": retraction_ref,
                "kind": "retraction",
                "logical_at": logical_at.isoformat(),
            }
        )
        return self._response(
            step,
            outcome="accepted",
            reason="retraction.recorded",
            state="retracted",
            output={"retraction_ref": retraction_ref},
            mutated=True,
        )

    def _action_deny_cross_scope(self, step, *, logical_at, identifiers):
        del logical_at, identifiers
        self.cross_scope_denied = True
        return self._response(
            step,
            outcome="denied",
            reason="authorization.cross_scope_denied",
            state="denied",
            output={"resource_disclosed": False},
        )

    def _action_degrade_worker(self, step, *, logical_at, identifiers):
        del logical_at, identifiers
        self.worker_state = "degraded"
        return self._response(
            step,
            outcome="degraded",
            reason="worker.degraded",
            state="worker_degraded",
            mutated=True,
        )

    def _action_recover_worker(self, step, *, logical_at, identifiers):
        del logical_at, identifiers
        if self.worker_state != "degraded":
            return self._response(
                step, outcome="denied", reason="worker.not_degraded", state="denied"
            )
        self.worker_state = "recovered"
        return self._response(
            step,
            outcome="recovered",
            reason="worker.recovered",
            state="recovered",
            mutated=True,
        )

    def _action_emit_signal(self, step, *, logical_at, identifiers):
        signal_ref = identifiers.issue(
            self.scenario_id, "signal", len(self.signals), prefix="ref"
        )
        self.signals.append(
            {
                "signal_ref": signal_ref,
                "logical_at": logical_at.isoformat(),
                "authoritative": False,
                "generated_only": True,
            }
        )
        return self._response(
            step,
            outcome="accepted",
            reason="signal.projected",
            state=self.terminal_state(),
            output={"signal_ref": signal_ref, "authoritative": False},
            mutated=True,
        )

    def terminal_state(self) -> str:
        if self.corrections and self.corrections[-1]["kind"] == "retraction":
            return "retracted"
        if self.worker_state == "recovered":
            return "recovered"
        if self.cross_scope_denied:
            return "denied"
        if self.conflict_recorded:
            return "conflict_recorded"
        if self.review_state == "denied":
            return "review_denied"
        if self.reference_state == "unavailable":
            return "reference_degraded"
        if self.rule_state == "not_matched" or self.reference_state == "abstained":
            return "abstained"
        if self.alerts and next(iter(self.alerts.values()))["state"] == "accepted":
            return "accepted"
        if self.alerts and next(iter(self.alerts.values()))["state"] == "closed":
            if self.investigations and self.evidence_references:
                return "completed"
            return "alert_closed"
        return "in_progress"

    def snapshot(self) -> Mapping[str, Any]:
        accepted_without_review = (
            any(
                item["state"] in {"accepted", "closed"} for item in self.alerts.values()
            )
            and not self.reviewed
        )
        return {
            "scenario_id": self.scenario_id,
            "events": list(self.events.values()),
            "hypotheses": list(self.hypotheses.values()),
            "alerts": list(self.alerts.values()),
            "investigations": list(self.investigations.values()),
            "evidence_references": list(self.evidence_references.values()),
            "signals": list(self.signals),
            "corrections": list(self.corrections),
            "conflict_recorded": self.conflict_recorded,
            "cross_scope_denied": self.cross_scope_denied,
            "reference_state": self.reference_state,
            "worker_state": self.worker_state,
            "rule_state": self.rule_state,
            "review_state": self.review_state,
            "accepted_without_review": accepted_without_review,
            "mutation_count": self._mutation_count,
            "direct_persistence_attempts": 0,
            "external_effects": 0,
            "generated_only": True,
            "operational": False,
        }
