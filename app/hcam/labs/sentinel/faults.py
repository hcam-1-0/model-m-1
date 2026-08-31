from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from time import time

from hcam.labs.sentinel.timing import FAULT_SCENARIOS


_CAMERA_ID = re.compile(r"^C(?:0[1-9]|[1-4][0-9]|50)$")
_REQUEST_ID = re.compile(r"^[0-9a-f]{32}$")
DEFAULT_FAULT_TARGETS = {
    "F1": "C01",
    "F2": "C02",
    "F3": "C11",
    "F4": "C11",
    "F5": "C12",
    "F6": "C04",
    "F7": "C09",
}


class FaultRequestError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class FaultRequest:
    request_id: str
    scenario: str
    camera_id: str
    requested_at_epoch: float
    duration_seconds: float
    classification: str = "generated-only"
    confirm_generated_only: bool = True

    @property
    def expires_at_epoch(self) -> float:
        return self.requested_at_epoch + self.duration_seconds

    def active(self, now: float | None = None) -> bool:
        instant = time() if now is None else now
        return self.requested_at_epoch <= instant < self.expires_at_epoch

    def document(self) -> dict[str, object]:
        result = asdict(self)
        result["expires_at_epoch"] = self.expires_at_epoch
        return result


def make_fault_request(
    scenario: str,
    *,
    camera_id: str | None = None,
    duration_seconds: float = 10,
    now: float | None = None,
) -> FaultRequest:
    if scenario not in FAULT_SCENARIOS:
        raise FaultRequestError("fault_scenario_not_allowed")
    selected_camera = camera_id or DEFAULT_FAULT_TARGETS[scenario]
    if _CAMERA_ID.fullmatch(selected_camera) is None:
        raise FaultRequestError("fault_camera_not_allowed")
    if not 1 <= duration_seconds <= 30:
        raise FaultRequestError("fault_duration_out_of_bounds")
    return FaultRequest(
        request_id=uuid.uuid4().hex,
        scenario=scenario,
        camera_id=selected_camera,
        requested_at_epoch=time() if now is None else now,
        duration_seconds=duration_seconds,
    )


def parse_fault_request(document: object) -> FaultRequest:
    if not isinstance(document, dict):
        raise FaultRequestError("fault_request_invalid")
    expected_keys = {
        "request_id",
        "scenario",
        "camera_id",
        "requested_at_epoch",
        "duration_seconds",
        "classification",
        "confirm_generated_only",
    }
    if set(document) != expected_keys:
        raise FaultRequestError("fault_request_invalid")
    request_id = document.get("request_id")
    scenario = document.get("scenario")
    camera_id = document.get("camera_id")
    requested_at = document.get("requested_at_epoch")
    duration = document.get("duration_seconds")
    if not isinstance(request_id, str) or _REQUEST_ID.fullmatch(request_id) is None:
        raise FaultRequestError("fault_request_invalid")
    if not isinstance(scenario, str) or scenario not in FAULT_SCENARIOS:
        raise FaultRequestError("fault_scenario_not_allowed")
    if not isinstance(camera_id, str) or _CAMERA_ID.fullmatch(camera_id) is None:
        raise FaultRequestError("fault_camera_not_allowed")
    if isinstance(requested_at, bool) or not isinstance(requested_at, int | float):
        raise FaultRequestError("fault_request_invalid")
    if isinstance(duration, bool) or not isinstance(duration, int | float):
        raise FaultRequestError("fault_request_invalid")
    if not 1 <= float(duration) <= 30:
        raise FaultRequestError("fault_duration_out_of_bounds")
    if (
        document.get("classification") != "generated-only"
        or document.get("confirm_generated_only") is not True
    ):
        raise FaultRequestError("generated_lab_confirmation_required")
    return FaultRequest(
        request_id=request_id,
        scenario=scenario,
        camera_id=camera_id,
        requested_at_epoch=float(requested_at),
        duration_seconds=float(duration),
    )


def read_fault_request(path: Path) -> FaultRequest | None:
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 16 * 1024:
        raise FaultRequestError("fault_request_file_invalid")
    try:
        document = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FaultRequestError("fault_request_invalid") from exc
    return parse_fault_request(document)


def atomic_write_json(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    os.replace(temporary, path)


def write_fault_request(path: Path, request: FaultRequest) -> None:
    document = request.document()
    document.pop("expires_at_epoch")
    atomic_write_json(path, document)
