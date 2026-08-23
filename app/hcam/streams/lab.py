from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import Camera
from hcam.streams.models import StreamEndpoint, StreamHealthCurrent


class SyntheticLabError(RuntimeError):
    pass


def synthetic_stream_id(number: int) -> str:
    if not 1 <= number <= 100:
        raise ValueError("synthetic stream number must be between 1 and 100")
    return f"str_{number:032x}"


def seed_synthetic_lab(session: Session, *, count: int = 50) -> dict[str, object]:
    if not 1 <= count <= 100:
        raise SyntheticLabError("synthetic lab count must be between 1 and 100")
    now = datetime.now(UTC)
    created_cameras = 0
    created_streams = 0
    with session.begin():
        for number in range(1, count + 1):
            stream_id = synthetic_stream_id(number)
            camera_id = f"phase2:cctv-{number:03d}"
            camera = session.get(Camera, camera_id)
            if camera is None:
                camera = Camera(
                    camera_id=camera_id,
                    source_id="phase2-synthetic",
                    external_id=f"cctv-{number:03d}",
                    display_name=f"Phase 2 Synthetic CCTV {number:03d}",
                    location_label="Disposable Phase 2 Lab",
                    timezone_name="Asia/Kolkata",
                    department="Engineering Lab",
                    ownership="H-CAM test fixture",
                    camera_type="synthetic",
                    connectivity_status="test-only",
                    health_status="unknown",
                    metadata_status="synthetic",
                    operational_status="test-only",
                    source_schema="hcam.phase2.synthetic.v1",
                    provenance={
                        "classification": "synthetic-only",
                        "real_person_footage": False,
                    },
                    imported_at=now,
                    created_at=now,
                    updated_at=now,
                )
                session.add(camera)
                created_cameras += 1
            elif camera.source_id != "phase2-synthetic":
                raise SyntheticLabError(f"camera ID collision at {camera_id}")

            endpoint = session.get(StreamEndpoint, stream_id)
            if endpoint is None:
                is_onvif_fixture = number == 1
                locator = (
                    "http://onvif-simulator:8081/onvif/media_service"
                    if is_onvif_fixture
                    else f"rtsp://mediamtx:8554/hcam/{stream_id}"
                )
                endpoint = StreamEndpoint(
                    stream_id=stream_id,
                    camera_id=camera_id,
                    name="primary",
                    adapter_kind="onvif" if is_onvif_fixture else "synthetic",
                    protocol="http" if is_onvif_fixture else "rtsp",
                    locator=locator,
                    management_locator=(
                        "http://onvif-simulator:8081/onvif/device_service"
                        if is_onvif_fixture
                        else None
                    ),
                    capability_refresh_enabled=is_onvif_fixture,
                    capability_due_at=now if is_onvif_fixture else None,
                    transport="tcp",
                    is_primary=True,
                    enabled=True,
                    probe_due_at=now,
                    created_at=now,
                    updated_at=now,
                )
                session.add(endpoint)
                session.add(
                    StreamHealthCurrent(
                        stream_id=stream_id,
                        state="unknown",
                        updated_at=now,
                    )
                )
                camera.selected_url = locator
                camera.delivery_type = endpoint.protocol
                camera.reachability = "unknown"
                created_streams += 1
            elif endpoint.camera_id != camera_id:
                raise SyntheticLabError(f"stream ID collision at {stream_id}")

        AuditRepository(session).record(
            actor_id="phase2-lab-seeder",
            action="phase2.lab.seed",
            target_type="synthetic_lab",
            target_id="phase2-50-stream-lab",
            source="hcam.cli",
            reason="Authorized disposable synthetic Phase 2 validation fixture",
            outcome="success",
            context={
                "count": count,
                "created_cameras": created_cameras,
                "created_streams": created_streams,
                "real_person_footage": False,
            },
            request_id=None,
        )
    return {
        "count": count,
        "created_cameras": created_cameras,
        "created_streams": created_streams,
        "mode": "synthetic-only",
    }
