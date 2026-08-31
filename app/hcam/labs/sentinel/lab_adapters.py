from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from hcam.labs.sentinel.faults import atomic_write_json


LabAdapterId = Literal["lab1highadapter", "lab2lowadapter"]


class LabAdapterStateError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class LabAdapterProfile:
    adapter_id: LabAdapterId
    label: str
    catalog_path: str
    generated_catalog_path: str
    record_count: int
    active_stream_count: int
    fixture_capacity: int
    resource_class: Literal["high", "low"]
    full_fidelity: bool
    catalog_capacity: int
    preview_session_limit: int
    inference_transport: Literal["rtsp_tcp"] = "rtsp_tcp"
    preview_transport: Literal["whep"] = "whep"
    quality_policy: Literal["native"] = "native"

    def document(self) -> dict[str, object]:
        return asdict(self)


LAB1_HIGH_ADAPTER = LabAdapterProfile(
    adapter_id="lab1highadapter",
    label="Lab 1 High",
    catalog_path="/api/ingest",
    generated_catalog_path="/api/ingest/lab1highadapter",
    record_count=50,
    active_stream_count=30,
    fixture_capacity=50,
    resource_class="high",
    full_fidelity=True,
    catalog_capacity=50,
    preview_session_limit=4,
)

LAB2_LOW_ADAPTER = LabAdapterProfile(
    adapter_id="lab2lowadapter",
    label="Lab 2 Low",
    catalog_path="/api/ingest",
    generated_catalog_path="/api/ingest/lab2lowadapter",
    record_count=12,
    active_stream_count=4,
    fixture_capacity=50,
    resource_class="low",
    full_fidelity=False,
    catalog_capacity=50,
    preview_session_limit=1,
)

LAB_ADAPTERS = (LAB1_HIGH_ADAPTER, LAB2_LOW_ADAPTER)
LAB_ADAPTER_BY_ID = {profile.adapter_id: profile for profile in LAB_ADAPTERS}
DEFAULT_LAB_ADAPTER = LAB1_HIGH_ADAPTER
LAB_ADAPTER_STATE_SCHEMA = "hcam.phase2_5.lab_adapter_state.v2"
_LEGACY_LAB_ADAPTER_STATE_SCHEMA = "hcam.phase2_5.lab_adapter_state.v1"


def lab_adapter_profile(adapter_id: str) -> LabAdapterProfile:
    try:
        return LAB_ADAPTER_BY_ID[adapter_id]  # type: ignore[index]
    except KeyError as exc:
        raise LabAdapterStateError("lab_adapter_unknown") from exc


def read_active_lab_adapter(path: Path) -> LabAdapterProfile:
    if not path.exists():
        return DEFAULT_LAB_ADAPTER
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 16 * 1024:
        raise LabAdapterStateError("lab_adapter_state_invalid")
    try:
        document = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LabAdapterStateError("lab_adapter_state_invalid") from exc
    if (
        not isinstance(document, dict)
        or document.get("schema")
        not in {LAB_ADAPTER_STATE_SCHEMA, _LEGACY_LAB_ADAPTER_STATE_SCHEMA}
        or document.get("classification")
        not in {"lab-profile-only", "generated-only"}
        or not isinstance(document.get("adapter_id"), str)
    ):
        raise LabAdapterStateError("lab_adapter_state_invalid")
    return lab_adapter_profile(document["adapter_id"])


def write_active_lab_adapter(path: Path, adapter_id: str) -> LabAdapterProfile:
    profile = lab_adapter_profile(adapter_id)
    atomic_write_json(
        path,
        {
            "schema": LAB_ADAPTER_STATE_SCHEMA,
            "classification": "lab-profile-only",
            "adapter_id": profile.adapter_id,
            "updated_at": datetime.now(UTC).isoformat(),
        },
    )
    return profile
