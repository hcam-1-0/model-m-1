#!/usr/bin/env python3
"""Run a bounded synthetic performance smoke for the Phase 1 registry API."""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from fastapi.testclient import TestClient

from hcam.camera_registry.importer import PayloadRegistryAdapter, RegistryImporter
from hcam.camera_registry.schemas import RegistrySeed
from hcam.main import create_app
from hcam.settings import Settings


REPORT_SCHEMA = "hcam.phase1.performance.v1"


def _synthetic_seed(camera_count: int) -> RegistrySeed:
    generated_at = datetime.now(UTC)
    return RegistrySeed.model_validate(
        {
            "schema": "hcam.camera_registry.seed.v1",
            "generated_at": generated_at.isoformat(),
            "source": {
                "adapter": "synthetic-performance",
                "safe_use": "Generated metadata only; no CCTV footage or Government data.",
            },
            "cameras": [
                {
                    "camera_id": f"synthetic:perf-{index:05d}",
                    "source": "synthetic-performance",
                    "external_id": f"perf-{index:05d}",
                    "display_name": f"Synthetic Performance Camera {index:05d}",
                    "department": f"synthetic-department-{index % 10}",
                    "camera_type": "synthetic-fixed",
                    "status": {"metadata": "available", "state": "synthetic"},
                    "stream": {"delivery": "metadata-only"},
                }
                for index in range(camera_count)
            ],
        }
    )


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _latency_summary(values: list[float]) -> dict[str, float]:
    return {
        "min_ms": round(min(values), 3),
        "median_ms": round(_percentile(values, 0.50), 3),
        "p95_ms": round(_percentile(values, 0.95), 3),
        "max_ms": round(max(values), 3),
    }


def run_performance_smoke(
    *,
    camera_count: int,
    iterations: int,
    max_p95_ms: float,
    max_import_seconds: float,
) -> dict[str, object]:
    if camera_count < 1 or iterations < 1:
        raise ValueError("camera count and iterations must be positive")
    if max_p95_ms <= 0 or max_import_seconds <= 0:
        raise ValueError("performance thresholds must be positive")

    with tempfile.TemporaryDirectory(prefix="hcam-performance-") as temp_dir:
        database_path = Path(temp_dir) / "performance.db"
        application = create_app(
            Settings(
                database_url=f"sqlite:///{database_path.as_posix()}",
                create_schema=True,
                dev_auth_enabled=True,
                environment="test",
                access_log_enabled=False,
            )
        )
        application.state.database.create_schema()
        seed = _synthetic_seed(camera_count)
        import_started = perf_counter()
        import_result = RegistryImporter(
            application.state.database.session_factory
        ).import_adapter(PayloadRegistryAdapter(seed, "synthetic-performance"))
        import_seconds = perf_counter() - import_started

        headers = {
            "X-HCAM-Actor": "performance-validator",
            "X-HCAM-Roles": "camera.viewer",
            "X-HCAM-Departments": "*",
        }
        list_latencies: list[float] = []
        detail_latencies: list[float] = []
        with TestClient(application) as client:
            for _ in range(3):
                assert client.get("/cameras?limit=100", headers=headers).status_code == 200
                assert (
                    client.get("/cameras/synthetic:perf-00000", headers=headers).status_code
                    == 200
                )
            for index in range(iterations):
                offset = (index * 100) % camera_count
                started = perf_counter()
                list_response = client.get(
                    f"/cameras?limit=100&offset={offset}",
                    headers=headers,
                )
                list_latencies.append((perf_counter() - started) * 1000)
                if list_response.status_code != 200:
                    raise RuntimeError("camera list performance request failed")

                camera_index = index % camera_count
                started = perf_counter()
                detail_response = client.get(
                    f"/cameras/synthetic:perf-{camera_index:05d}",
                    headers=headers,
                )
                detail_latencies.append((perf_counter() - started) * 1000)
                if detail_response.status_code != 200:
                    raise RuntimeError("camera detail performance request failed")

        list_summary = _latency_summary(list_latencies)
        detail_summary = _latency_summary(detail_latencies)
        passed = (
            import_seconds <= max_import_seconds
            and list_summary["p95_ms"] <= max_p95_ms
            and detail_summary["p95_ms"] <= max_p95_ms
        )
        return {
            "schema": REPORT_SCHEMA,
            "passed": passed,
            "dataset": {
                "camera_count": camera_count,
                "synthetic_only": True,
                "video_used": False,
            },
            "import": {
                "created": import_result.created,
                "elapsed_seconds": round(import_seconds, 3),
                "max_seconds": max_import_seconds,
            },
            "requests_per_operation": iterations,
            "list": list_summary,
            "detail": detail_summary,
            "max_p95_ms": max_p95_ms,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cameras", type=int, default=1000)
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--max-p95-ms", type=float, default=750.0)
    parser.add_argument("--max-import-seconds", type=float, default=20.0)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run_performance_smoke(
            camera_count=args.cameras,
            iterations=args.iterations,
            max_p95_ms=args.max_p95_ms,
            max_import_seconds=args.max_import_seconds,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Phase 1 performance smoke failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            "Phase 1 performance: "
            f"{'pass' if report['passed'] else 'fail'}; "
            f"cameras={report['dataset']['camera_count']}; "
            f"list_p95_ms={report['list']['p95_ms']}; "
            f"detail_p95_ms={report['detail']['p95_ms']}"
        )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
