#!/usr/bin/env python3
"""Run a bounded concurrent load smoke against a loopback Phase 1 API."""

from __future__ import annotations

import argparse
import json
import math
import socket
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic, perf_counter, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import uvicorn

from hcam.camera_registry.importer import PayloadRegistryAdapter, RegistryImporter
from hcam.camera_registry.schemas import RegistrySeed
from hcam.main import create_app
from hcam.settings import Settings


REPORT_SCHEMA = "hcam.phase1.concurrent-load.v1"
_VIEWER_HEADERS = {
    "X-HCAM-Actor": "concurrent-load-validator",
    "X-HCAM-Roles": "camera.viewer",
    "X-HCAM-Departments": "*",
}


def _synthetic_seed(camera_count: int) -> RegistrySeed:
    generated_at = datetime.now(UTC)
    return RegistrySeed.model_validate(
        {
            "schema": "hcam.camera_registry.seed.v1",
            "generated_at": generated_at.isoformat(),
            "source": {
                "adapter": "synthetic-concurrent-load",
                "safe_use": "Generated metadata only; no CCTV footage or Government data.",
            },
            "cameras": [
                {
                    "camera_id": f"synthetic:load-{index:05d}",
                    "source": "synthetic-concurrent-load",
                    "external_id": f"load-{index:05d}",
                    "display_name": f"Synthetic Load Camera {index:05d}",
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


def _request(base_url: str, path: str) -> tuple[int, float]:
    started = perf_counter()
    request = Request(f"{base_url}{path}", headers=_VIEWER_HEADERS)
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310 - loopback only
            response.read()
            status_code = response.status
    except HTTPError as exc:
        exc.read()
        status_code = exc.code
    except (OSError, URLError):
        status_code = 0
    return status_code, (perf_counter() - started) * 1000


def _start_server(application) -> tuple[uvicorn.Server, threading.Thread, int]:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(2048)
    port = int(listener.getsockname()[1])
    server = uvicorn.Server(
        uvicorn.Config(
            application,
            log_level="critical",
            access_log=False,
            lifespan="on",
        )
    )
    thread = threading.Thread(
        target=server.run,
        kwargs={"sockets": [listener]},
        name="hcam-phase1-load-server",
        daemon=True,
    )
    thread.start()
    deadline = monotonic() + 10
    while not server.started and thread.is_alive() and monotonic() < deadline:
        sleep(0.01)
    if not server.started:
        server.should_exit = True
        thread.join(timeout=5)
        listener.close()
        raise RuntimeError("loopback load server did not start")
    return server, thread, port


def _stop_server(server: uvicorn.Server, thread: threading.Thread) -> None:
    server.should_exit = True
    thread.join(timeout=10)
    if thread.is_alive():
        server.force_exit = True
        thread.join(timeout=5)
    if thread.is_alive():
        raise RuntimeError("loopback load server did not stop")


def run_concurrent_load_smoke(
    *,
    camera_count: int,
    request_count: int,
    concurrency: int,
    max_p95_ms: float,
    max_error_rate: float,
) -> dict[str, object]:
    if camera_count < 1 or request_count < 1 or concurrency < 1:
        raise ValueError("camera, request, and concurrency counts must be positive")
    if concurrency > request_count:
        raise ValueError("concurrency must not exceed request count")
    if (
        not math.isfinite(max_p95_ms)
        or not math.isfinite(max_error_rate)
        or max_p95_ms <= 0
        or not 0 <= max_error_rate <= 1
    ):
        raise ValueError("load thresholds are invalid")

    with tempfile.TemporaryDirectory(prefix="hcam-concurrent-load-") as temp_dir:
        database_path = Path(temp_dir) / "load.db"
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
        RegistryImporter(application.state.database.session_factory).import_adapter(
            PayloadRegistryAdapter(seed, "synthetic-concurrent-load")
        )

        server, server_thread, port = _start_server(application)
        base_url = f"http://127.0.0.1:{port}"
        try:
            warm_status, _ = _request(base_url, "/cameras?limit=1")
            if warm_status != 200:
                raise RuntimeError("loopback load warmup failed")
            paths = []
            for index in range(request_count):
                if index % 2 == 0:
                    offset = (index * 10) % camera_count
                    paths.append(f"/cameras?limit=10&offset={offset}")
                else:
                    camera_index = index % camera_count
                    paths.append(f"/cameras/synthetic:load-{camera_index:05d}")

            started = perf_counter()
            results: list[tuple[int, float]] = []
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(_request, base_url, path) for path in paths]
                for future in as_completed(futures):
                    results.append(future.result())
            elapsed_seconds = perf_counter() - started
        finally:
            _stop_server(server, server_thread)

        statuses = [status_code for status_code, _ in results]
        latencies = [latency for _, latency in results]
        errors = sum(status_code != 200 for status_code in statuses)
        error_rate = errors / request_count
        latency = _latency_summary(latencies)
        passed = error_rate <= max_error_rate and latency["p95_ms"] <= max_p95_ms
        return {
            "schema": REPORT_SCHEMA,
            "passed": passed,
            "scope": {
                "transport": "loopback-http",
                "synthetic_only": True,
                "video_used": False,
                "external_network_used": False,
            },
            "dataset": {"camera_count": camera_count},
            "load": {
                "request_count": request_count,
                "concurrency": concurrency,
                "elapsed_seconds": round(elapsed_seconds, 3),
                "requests_per_second": round(request_count / elapsed_seconds, 3),
                "errors": errors,
                "error_rate": round(error_rate, 6),
                "max_error_rate": max_error_rate,
            },
            "latency": latency,
            "max_p95_ms": max_p95_ms,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cameras", type=int, default=1000)
    parser.add_argument("--requests", type=int, default=400)
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--max-p95-ms", type=float, default=1500.0)
    parser.add_argument("--max-error-rate", type=float, default=0.0)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run_concurrent_load_smoke(
            camera_count=args.cameras,
            request_count=args.requests,
            concurrency=args.concurrency,
            max_p95_ms=args.max_p95_ms,
            max_error_rate=args.max_error_rate,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Phase 1 concurrent load smoke failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            "Phase 1 concurrent load: "
            f"{'pass' if report['passed'] else 'fail'}; "
            f"requests={report['load']['request_count']}; "
            f"concurrency={report['load']['concurrency']}; "
            f"p95_ms={report['latency']['p95_ms']}; "
            f"error_rate={report['load']['error_rate']}"
        )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
