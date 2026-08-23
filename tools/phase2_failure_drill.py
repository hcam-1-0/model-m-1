#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from phase2_lab import (
    DEFAULT_SECRET_ROOT,
    LabError,
    compose,
    load_metrics_token,
    verify_metrics,
)


VIEW_HEADERS = {
    "X-HCAM-Actor": "phase2-failure-drill",
    "X-HCAM-Roles": "camera.editor",
    "X-HCAM-Departments": "*",
}


def _request(url: str, *, method: str = "GET", reason: bool = False) -> dict:
    headers = dict(VIEW_HEADERS)
    if reason:
        headers["X-HCAM-Reason"] = "Authorized synthetic stream recovery drill"
    try:
        with urlopen(Request(url, method=method, headers=headers), timeout=10) as response:
            payload = response.read(1024 * 1024)
    except HTTPError:
        raise
    except (URLError, TimeoutError, OSError) as exc:
        raise LabError("failure drill API request failed") from exc
    document = json.loads(payload)
    if not isinstance(document, dict):
        raise LabError("failure drill API response was invalid")
    return document


def _wait_for(
    url: str,
    predicate,
    *,
    timeout: float,
) -> dict:
    deadline = monotonic() + timeout
    latest: dict = {}
    while monotonic() < deadline:
        latest = _request(url)
        if predicate(latest):
            return latest
        sleep(1)
    raise LabError(f"failure drill transition timed out; last state={latest.get('state')}")


def _queue_probe(api_url: str, stream_id: str) -> None:
    deadline = monotonic() + 30
    while monotonic() < deadline:
        try:
            _request(
                f"{api_url}/streams/{stream_id}/probe",
                method="POST",
                reason=True,
            )
            return
        except HTTPError as exc:
            if exc.code != 409:
                raise LabError(f"probe queue failed with HTTP {exc.code}") from exc
            sleep(0.5)
    raise LabError("probe queue remained leased for 30 seconds")


def _inventory_items(api_url: str) -> list[dict]:
    inventory = _request(f"{api_url}/streams?limit=100")
    items = inventory.get("items")
    if not isinstance(items, list) or len(items) != 50:
        raise LabError("the 50-stream inventory is unavailable")
    if not all(
        isinstance(item, dict) and isinstance(item.get("stream_id"), str)
        for item in items
    ):
        raise LabError("stream inventory contains an invalid item")
    return items


def _recover_fleet(api_url: str, *, timeout: float) -> int:
    items = _inventory_items(api_url)
    stream_ids = [item["stream_id"] for item in items]
    for _round in range(2):
        before = {
            item["stream_id"]: (item.get("health") or {}).get("observed_at")
            for item in items
        }
        for stream_id in stream_ids:
            _queue_probe(api_url, stream_id)
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            items = _inventory_items(api_url)
            if all(
                isinstance(item.get("health"), dict)
                and item["health"].get("observed_at") != before[item["stream_id"]]
                and int(item["health"].get("consecutive_successes", 0)) >= 1
                for item in items
            ):
                break
            sleep(1)
        else:
            states = {
                str((item.get("health") or {}).get("state")) for item in items
            }
            raise LabError(
                f"full fleet did not complete a successful recovery round; states={states}"
            )
    unhealthy = [
        item["stream_id"]
        for item in items
        if (item.get("health") or {}).get("state") != "healthy"
    ]
    if unhealthy:
        raise LabError(f"full fleet recovery left {len(unhealthy)} unhealthy streams")
    return len(items)


def run_drill(
    secret_root: Path,
    *,
    api_url: str,
    transition_timeout: float,
) -> dict[str, object]:
    base = api_url.rstrip("/")
    items = _inventory_items(base)
    target = next(
        (
            item
            for item in items
            if isinstance(item, dict)
            and item.get("adapter_kind") == "onvif"
            and isinstance(item.get("health"), dict)
            and item["health"].get("state") == "healthy"
        ),
        None,
    )
    if target is None or not isinstance(target.get("stream_id"), str):
        raise LabError("no healthy ONVIF synthetic stream is available for the drill")
    stream_id = target["stream_id"]
    health_url = f"{base}/streams/{stream_id}/health"
    compose(secret_root, "stop", "onvif-simulator")
    simulator_restarted = False
    try:
        for expected_failures in range(1, 4):
            _queue_probe(base, stream_id)
            _wait_for(
                health_url,
                lambda value, expected=expected_failures: int(
                    value.get("consecutive_failures", 0)
                )
                >= expected,
                timeout=transition_timeout,
            )
        offline = _request(health_url)
        if offline.get("state") != "offline":
            raise LabError("three transient failures did not move the stream offline")

        compose(secret_root, "start", "onvif-simulator")
        simulator_restarted = True
        sleep(5)
        for expected_successes in range(1, 3):
            _queue_probe(base, stream_id)
            _wait_for(
                health_url,
                lambda value, expected=expected_successes: int(
                    value.get("consecutive_successes", 0)
                )
                >= expected,
                timeout=transition_timeout,
            )
        recovered = _request(health_url)
        if recovered.get("state") != "healthy":
            raise LabError("two consecutive successes did not restore healthy state")
        fleet_recovered = _recover_fleet(
            base,
            timeout=max(120.0, transition_timeout * 2),
        )
        metrics = verify_metrics(
            base,
            load_metrics_token(secret_root),
        )
        return {
            "passed": True,
            "stream_id": stream_id,
            "fault_injection": "controlled-onvif-simulator-outage",
            "fleet_recovered": fleet_recovered,
            "failure_transition": "healthy->degraded->offline",
            "recovery_transition": "offline->degraded->healthy",
            "recording_used": False,
            "real_video_used": False,
            **metrics,
        }
    finally:
        if not simulator_restarted:
            compose(secret_root, "start", "onvif-simulator")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 2 synthetic failure drill")
    parser.add_argument("--secret-root", type=Path, default=DEFAULT_SECRET_ROOT)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--transition-timeout", type=float, default=45)
    args = parser.parse_args(argv)
    try:
        report = run_drill(
            args.secret_root,
            api_url=args.api_url,
            transition_timeout=args.transition_timeout,
        )
    except (LabError, HTTPError, json.JSONDecodeError) as exc:
        print(f"phase2 failure drill failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
