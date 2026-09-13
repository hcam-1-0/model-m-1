from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from hcam.intelligence.rules.cel_adapter import (
    ConstrainedRuleCelEnvironment,
    RuleCelError,
)
from hcam.intelligence.rules.compiler import compile_rule
from hcam.intelligence.rules.contracts import RuleScheduleV1, VisualRuleDocumentV1
from hcam.intelligence.rules.temporal import (
    TemporalToken,
    ordered_sequence,
    schedule_is_open,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "contracts" / "phase-4" / "p4-2" / "fixtures"
FIXTURES = {
    "generated-cel-cases-v1.json": "hcam.p4-2.generated-cel-cases.v1",
    "generated-corrections-v1.json": "hcam.p4-2.generated-corrections.v1",
    "generated-rule-canonicalization-v1.json": (
        "hcam.p4-2.generated-rule-canonicalization.v1"
    ),
    "generated-rule-documents-v1.json": "hcam.p4-2.generated-rule-documents.v1",
    "generated-schedule-dst-v1.json": "hcam.p4-2.generated-schedule-dst.v1",
    "generated-shadow-comparisons-v1.json": (
        "hcam.p4-2.generated-shadow-comparisons.v1"
    ),
    "generated-temporal-sequences-v1.json": (
        "hcam.p4-2.generated-temporal-sequences.v1"
    ),
}


def _load(name: str) -> dict[str, Any]:
    path = FIXTURE_ROOT / name
    raw = path.read_bytes()
    if len(raw) > 128 * 1024 or raw.decode("ascii").encode("ascii") != raw:
        raise ValueError("generated fixture encoding or size is invalid")
    value = json.loads(raw)
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != FIXTURES[name]
        or value.get("generated_only") is not True
    ):
        raise ValueError("generated fixture contract is invalid")
    return value


def validate_fixtures() -> dict[str, int]:
    fixtures = {name: _load(name) for name in FIXTURES}
    documents = [
        VisualRuleDocumentV1.model_validate(item)
        for item in fixtures["generated-rule-documents-v1.json"]["documents"]
    ]
    for document in documents:
        first = compile_rule(document)
        second = compile_rule(document)
        if (
            first.compilation != second.compilation
            or first.canonical_bytes != second.canonical_bytes
        ):
            raise ValueError("generated compilation is not deterministic")

    cel = ConstrainedRuleCelEnvironment()
    cel_cases = fixtures["generated-cel-cases-v1.json"]
    for index, source in enumerate(cel_cases["accepted"]):
        first = cel.compile(source, f"n{index:03d}")
        second = cel.compile(source, f"n{index:03d}")
        if first.serialized != second.serialized:
            raise ValueError("generated CEL compilation is not deterministic")
    for index, source in enumerate(cel_cases["rejected"]):
        try:
            cel.compile(source, f"r{index:03d}")
        except (RuleCelError, ValueError):
            continue
        raise ValueError("generated rejected CEL case compiled")

    temporal_cases = fixtures["generated-temporal-sequences-v1.json"]["cases"]
    base = datetime.fromisoformat("2026-01-01T00:00:00+00:00")
    for case in temporal_cases:
        stages = tuple(
            tuple(
                TemporalToken(
                    f"generated-{stage}-{second}",
                    base + timedelta(seconds=second),
                    "str_" + "1" * 32,
                )
                for second in seconds
            )
            for stage, seconds in enumerate(case["input_seconds"])
        )
        result = ordered_sequence(stages, maximum_span_ms=case["maximum_span_ms"])
        if result.reason_code != case["expected"]:
            raise ValueError("generated temporal case does not match")

    schedule_cases = fixtures["generated-schedule-dst-v1.json"]["cases"]
    for case in schedule_cases:
        schedule = RuleScheduleV1(
            schedule_id=f"generated.{case['case_id']}",
            timezone=case["timezone"],
            timezone_data_version="tzdata.2026c",
            intervals=[
                {
                    "weekday": case["weekday"],
                    "start_minute": case["start_minute"],
                    "end_minute": case["end_minute"],
                }
            ],
        )
        instant = datetime.fromisoformat(case["instant"].replace("Z", "+00:00"))
        if schedule_is_open(schedule, instant) is not case["expected_open"]:
            raise ValueError("generated schedule case does not match")

    corrections = fixtures["generated-corrections-v1.json"]
    if (
        corrections["allowed_revision_reasons"]
        != [
            "late_input",
            "superseded",
            "retracted",
            "replay",
        ]
        or corrections["history_policy"] != "append_only"
    ):
        raise ValueError("generated correction policy is invalid")
    shadow = fixtures["generated-shadow-comparisons-v1.json"]
    if shadow.get("operational") is not False or any(
        min(
            case["candidate_matches"],
            case["baseline_matches"],
            case["disagreement_count"],
        )
        < 0
        for case in shadow["cases"]
    ):
        raise ValueError("generated shadow comparison is invalid")
    return {
        "fixtures": len(fixtures),
        "documents": len(documents),
        "cel_cases": len(cel_cases["accepted"]) + len(cel_cases["rejected"]),
        "temporal_cases": len(temporal_cases),
        "schedule_cases": len(schedule_cases),
        "shadow_cases": len(shadow["cases"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate repository-owned generated-only P4.2 rule fixtures."
    )
    parser.add_argument("command", choices=("check", "run"))
    parser.parse_args()
    try:
        summary = validate_fixtures()
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "passed": False,
                    "failure_code": "generated_fixture_validation_failed",
                    "detail": type(exc).__name__,
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return 1
    result = {"passed": True, "generated_only": True, **summary}
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
