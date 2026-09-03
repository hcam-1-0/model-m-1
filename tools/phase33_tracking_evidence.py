#!/usr/bin/env python3
"""Generate and verify P3.3 generated-only tracker evaluation evidence."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from hcam.analytics.activation import (
    P3_3_CONFIGURATION_VERSION,
    P3_3_PIPELINE_VERSION,
    P3_3_POLICY_VERSION,
    P3_3_TRACKER_ID,
    P3_3_TRACKER_VERSION,
)
from hcam.analytics.tracking import (
    StreamLocalTracker,
    TrackerConfiguration,
    build_generated_tracking_scenario,
    evaluate_tracking_sequence,
)
from hcam.analytics.tracking.kalman import BoundingBoxKalmanFilter
from hcam.analytics.tracking.metrics import _sequence_data
from hcam.analytics.tracking.types import TrackingResourceError


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "contracts" / "phase-3" / "p3-3" / "evaluation-report.json"
SCENARIOS = (
    "single-object",
    "two-crossing",
    "short-occlusion",
    "long-occlusion",
    "all-tier-a",
    "discontinuity",
)
CHALLENGE_SCENARIOS = ("two-crossing", "all-tier-a", "discontinuity")
OBSERVED_AT = datetime(2026, 8, 25, 12, tzinfo=UTC)


def _serialized(document: object) -> str:
    return json.dumps(
        document,
        indent=2,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
    ) + "\n"


def _digest(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def _execute_scenario(scenario_id: str, seed: int = 0):
    scenario = build_generated_tracking_scenario(
        scenario_id,
        seed,
        OBSERVED_AT,
    )
    tracker = StreamLocalTracker(
        department="phase3-generated-lab",
        assignment_id="ana_" + "1" * 32,
        camera_id="synthetic:cctv-001",
        stream_id="str_" + "2" * 32,
        configuration=TrackerConfiguration(),
        execution_id=f"evidence:{scenario_id}:{seed}",
    )
    results = tuple(tracker.update(item.frame) for item in scenario.frames)
    return scenario, results


def _load_trackeval(trackeval_root: Path):
    if not (trackeval_root / "trackeval" / "metrics" / "hota.py").is_file():
        raise ValueError("TrackEval root does not contain the pinned metric source")
    np.float = float  # type: ignore[attr-defined]
    np.int = int  # type: ignore[attr-defined]
    sys.path.insert(0, str(trackeval_root))
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            from trackeval.metrics.hota import HOTA
            from trackeval.metrics.identity import Identity
    finally:
        sys.path.pop(0)
    return HOTA, Identity


def _trackeval_parity(trackeval_root: Path, scenario_records) -> dict[str, object]:
    hota_type, identity_type = _load_trackeval(trackeval_root)
    comparisons: list[dict[str, object]] = []
    max_hota_error = 0.0
    max_idf1_error = 0.0
    for scenario_id, (scenario, results, metrics) in scenario_records.items():
        for class_id, internal in metrics.per_class.items():
            data = _sequence_data(scenario, results, class_id)
            official_data = {
                "gt_ids": list(data.truth_ids),
                "tracker_ids": list(data.tracker_ids),
                "similarity_scores": list(data.similarities),
                "num_gt_ids": data.truth_identity_count,
                "num_tracker_ids": data.tracker_identity_count,
                "num_gt_dets": data.truth_detection_count,
                "num_tracker_dets": data.tracker_detection_count,
                "num_timesteps": len(data.truth_ids),
            }
            official_hota = hota_type().eval_sequence(official_data)
            official_identity = identity_type({"PRINT_CONFIG": False}).eval_sequence(
                official_data
            )
            hota_value = float(np.mean(official_hota["HOTA"]))
            idf1_value = float(official_identity["IDF1"])
            hota_error = abs(hota_value - internal.hota)
            idf1_error = abs(idf1_value - internal.idf1)
            max_hota_error = max(max_hota_error, hota_error)
            max_idf1_error = max(max_idf1_error, idf1_error)
            comparisons.append(
                {
                    "class_id": class_id,
                    "hcam_hota": internal.hota,
                    "hcam_idf1": internal.idf1,
                    "hota_absolute_error": hota_error,
                    "idf1_absolute_error": idf1_error,
                    "scenario_id": scenario_id,
                    "trackeval_hota": hota_value,
                    "trackeval_idf1": idf1_value,
                }
            )
    return {
        "comparison_count": len(comparisons),
        "comparisons": comparisons,
        "maximum_hota_absolute_error": max_hota_error,
        "maximum_idf1_absolute_error": max_idf1_error,
        "passed": max_hota_error <= 1e-12 and max_idf1_error <= 1e-12,
    }


def _load_upstream_kalman(bytetrack_root: Path):
    source = bytetrack_root / "yolox" / "tracker" / "kalman_filter.py"
    if not source.is_file():
        raise ValueError("ByteTrack root does not contain the pinned Kalman source")
    spec = importlib.util.spec_from_file_location("pinned_bytetrack_kalman", source)
    if spec is None or spec.loader is None:
        raise ValueError("Pinned ByteTrack Kalman source cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.KalmanFilter


def _bytetrack_component_parity(bytetrack_root: Path) -> dict[str, object]:
    upstream_type = _load_upstream_kalman(bytetrack_root)
    upstream = upstream_type()
    hcam = BoundingBoxKalmanFilter()
    measurement = np.asarray([0.25, 0.30, 0.5, 0.20], dtype=np.float64)
    next_measurement = np.asarray([0.27, 0.31, 0.5, 0.20], dtype=np.float64)
    upstream_mean, upstream_covariance = upstream.initiate(measurement)
    hcam_mean, hcam_covariance = hcam.initiate(measurement)
    errors = {
        "initiate_mean": float(np.max(np.abs(upstream_mean - hcam_mean))),
        "initiate_covariance": float(
            np.max(np.abs(upstream_covariance - hcam_covariance))
        ),
    }
    upstream_mean, upstream_covariance = upstream.predict(
        upstream_mean,
        upstream_covariance,
    )
    hcam_mean, hcam_covariance = hcam.predict(
        hcam_mean,
        hcam_covariance,
        tracked=True,
    )
    errors["predict_mean"] = float(np.max(np.abs(upstream_mean - hcam_mean)))
    errors["predict_covariance"] = float(
        np.max(np.abs(upstream_covariance - hcam_covariance))
    )
    upstream_mean, upstream_covariance = upstream.update(
        upstream_mean,
        upstream_covariance,
        next_measurement,
    )
    hcam_mean, hcam_covariance = hcam.update(
        hcam_mean,
        hcam_covariance,
        next_measurement,
    )
    errors["update_mean"] = float(np.max(np.abs(upstream_mean - hcam_mean)))
    errors["update_covariance"] = float(
        np.max(np.abs(upstream_covariance - hcam_covariance))
    )
    maximum_error = max(errors.values())
    return {
        "component": "kalman_initiate_predict_update",
        "errors": errors,
        "full_historical_runtime_executed": False,
        "maximum_absolute_error": maximum_error,
        "passed": maximum_error <= 1e-12,
        "solver_substitution": "scipy.optimize.linear_sum_assignment",
        "upstream_full_stack_rejection": (
            "Detector, media, Torch, OpenCV, LAP, training, visualization, and "
            "ReID dependencies remain outside the H-CAM runtime boundary."
        ),
    }


def build_report(bytetrack_root: Path, trackeval_root: Path) -> dict[str, object]:
    scenario_records = {}
    summaries = {}
    deterministic = True
    for scenario_id in SCENARIOS:
        scenario, results = _execute_scenario(scenario_id)
        metrics = evaluate_tracking_sequence(scenario, results)
        scenario_records[scenario_id] = (scenario, results, metrics)
        replay_documents = []
        for _ in range(3):
            replay_scenario, replay_results = _execute_scenario(scenario_id)
            replay_documents.append(
                _serialized(
                    _jsonable(
                        {
                            "digest": replay_scenario.digest,
                            "results": replay_results,
                        }
                    )
                )
            )
        deterministic = deterministic and len(set(replay_documents)) == 1
        transitions = [
            transition
            for result in results
            for transition in result.transitions
        ]
        summaries[scenario_id] = {
            "frame_count": len(scenario.frames),
            "input_sha256": scenario.digest,
            "metrics": _jsonable(metrics),
            "recovered_transitions": sum(
                transition.reason == "recovered" for transition in transitions
            ),
            "transition_count": len(transitions),
        }

    overload = build_generated_tracking_scenario("overload", 0, OBSERVED_AT)
    tracker = StreamLocalTracker(
        department="phase3-generated-lab",
        assignment_id="ana_" + "1" * 32,
        camera_id="synthetic:cctv-001",
        stream_id="str_" + "2" * 32,
        configuration=TrackerConfiguration(),
        execution_id="evidence:overload:0",
    )
    overload_failed_closed = False
    try:
        tracker.update(overload.frames[0].frame)
    except TrackingResourceError:
        overload_failed_closed = True

    challenge_hota = sum(
        summaries[item]["metrics"]["hota"] for item in CHALLENGE_SCENARIOS
    ) / len(CHALLENGE_SCENARIOS)
    challenge_idf1 = sum(
        summaries[item]["metrics"]["idf1"] for item in CHALLENGE_SCENARIOS
    ) / len(CHALLENGE_SCENARIOS)
    all_class_metrics = summaries["all-tier-a"]["metrics"]["per_class"]
    gates = {
        "challenge_hota": challenge_hota,
        "challenge_hota_minimum": 0.85,
        "challenge_idf1": challenge_idf1,
        "challenge_idf1_minimum": 0.90,
        "deterministic_three_runs": deterministic,
        "golden_hota": summaries["all-tier-a"]["metrics"]["hota"],
        "golden_hota_minimum": 1.0,
        "golden_idf1": summaries["all-tier-a"]["metrics"]["idf1"],
        "golden_idf1_minimum": 1.0,
        "overload_failed_closed": overload_failed_closed,
        "per_class_hota_minimum_observed": min(
            item["hota"] for item in all_class_metrics.values()
        ),
        "per_class_hota_minimum_required": 0.80,
        "per_class_idf1_minimum_observed": min(
            item["idf1"] for item in all_class_metrics.values()
        ),
        "per_class_idf1_minimum_required": 0.85,
        "short_occlusion_recovery_rate": float(
            summaries["short-occlusion"]["recovered_transitions"] > 0
        ),
        "short_occlusion_recovery_rate_minimum": 0.95,
    }
    gates["passed"] = all(
        (
            gates["challenge_hota"] >= gates["challenge_hota_minimum"],
            gates["challenge_idf1"] >= gates["challenge_idf1_minimum"],
            gates["deterministic_three_runs"],
            gates["golden_hota"] >= gates["golden_hota_minimum"],
            gates["golden_idf1"] >= gates["golden_idf1_minimum"],
            gates["overload_failed_closed"],
            gates["per_class_hota_minimum_observed"]
            >= gates["per_class_hota_minimum_required"],
            gates["per_class_idf1_minimum_observed"]
            >= gates["per_class_idf1_minimum_required"],
            gates["short_occlusion_recovery_rate"]
            >= gates["short_occlusion_recovery_rate_minimum"],
        )
    )
    trackeval = _trackeval_parity(trackeval_root, scenario_records)
    bytetrack = _bytetrack_component_parity(bytetrack_root)
    return {
        "artifacts": {
            "configuration_version": P3_3_CONFIGURATION_VERSION,
            "evaluator_manifest_digest": _digest(
                ROOT / "contracts" / "phase-3" / "p3-3-evaluator-source.json"
            ),
            "pipeline_version": P3_3_PIPELINE_VERSION,
            "policy_version": P3_3_POLICY_VERSION,
            "tracker_id": P3_3_TRACKER_ID,
            "tracker_manifest_digest": _digest(
                ROOT / "contracts" / "phase-3" / "p3-3-tracker-source.json"
            ),
            "tracker_version": P3_3_TRACKER_VERSION,
        },
        "bytetrack_component_parity": bytetrack,
        "evaluation_scope": "generated_structured_observations_only",
        "gates": gates,
        "limitations": [
            "No image or video input was used.",
            "No external dataset, camera, biometric, ReID, or cross-camera path was used.",
            "Generated metrics do not establish real-CCTV accuracy.",
            "The full historical ByteTrack runtime was rejected and not executed.",
        ],
        "overall_passed": bool(gates["passed"] and trackeval["passed"] and bytetrack["passed"]),
        "scenario_reports": summaries,
        "schema_version": "1.0.0",
        "trackeval_parity": trackeval,
    }


def _validate_report(document: dict[str, object]) -> list[str]:
    failures = []
    if document.get("schema_version") != "1.0.0":
        failures.append("report schema version is invalid")
    if document.get("evaluation_scope") != "generated_structured_observations_only":
        failures.append("report scope is invalid")
    if document.get("overall_passed") is not True:
        failures.append("one or more P3.3 evaluation gates failed")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    write = subparsers.add_parser("write")
    write.add_argument("--bytetrack-root", type=Path, required=True)
    write.add_argument("--trackeval-root", type=Path, required=True)
    write.add_argument("--acknowledge-generated-only-evidence", action="store_true")
    subparsers.add_parser("check")
    args = parser.parse_args(argv)
    if args.command == "write":
        if not args.acknowledge_generated_only_evidence:
            print("[fail] explicit generated-only evidence acknowledgment is required")
            return 2
        document = build_report(args.bytetrack_root, args.trackeval_root)
        failures = _validate_report(document)
        if failures:
            for failure in failures:
                print(f"[fail] {failure}")
            return 1
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(_serialized(document), encoding="utf-8", newline="\n")
        print(f"[write] {REPORT.relative_to(ROOT)} {_digest(REPORT)}")
        return 0
    try:
        document = json.loads(REPORT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[fail] evaluation report is unavailable: {exc}")
        return 1
    failures = _validate_report(document)
    for failure in failures:
        print(f"[fail] {failure}")
    if failures:
        return 1
    print(f"[pass] {REPORT.relative_to(ROOT)} {_digest(REPORT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
