from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


CameraId = Annotated[
    str,
    Field(
        min_length=3,
        max_length=160,
        pattern=r"^[a-z][a-z0-9._-]*:[A-Za-z0-9][A-Za-z0-9._:-]*$",
    ),
]
SourceId = Annotated[
    str,
    Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9-]*$"),
]
NonEmptyText = Annotated[str, Field(min_length=1)]


class LocationSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, max_length=500)
    timezone: str | None = Field(default=None, max_length=80)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def coordinates_are_a_pair(self) -> LocationSeed:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        return self


class CameraStatusSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=80)


class StreamSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stream_path: str | None = None
    hls_path: str | None = None
    stream_url: str | None = None
    hls_url: str | None = None
    selected_url: str | None = None
    delivery: str | None = Field(default=None, max_length=80)
    codec: str | None = Field(default=None, max_length=80)
    container: str | None = Field(default=None, max_length=80)
    duration_seconds: float | None = Field(default=None, ge=0)
    reachability: str | None = Field(default=None, max_length=80)
    last_checked_at: datetime | None = None


class CameraSeed(BaseModel):
    # Adapter-specific fields may be present but never enter the normalized model.
    model_config = ConfigDict(extra="ignore")

    camera_id: CameraId
    source: SourceId
    external_id: Annotated[str, Field(min_length=1, max_length=255)]
    display_name: Annotated[str, Field(min_length=1, max_length=255)]
    location: LocationSeed = Field(default_factory=LocationSeed)
    status: CameraStatusSeed = Field(default_factory=CameraStatusSeed)
    stream: StreamSeed = Field(default_factory=StreamSeed)
    department: str | None = Field(default=None, max_length=120)
    ownership: str | None = Field(default=None, max_length=120)
    camera_type: str | None = Field(default=None, max_length=80)
    connectivity_status: str | None = Field(default=None, max_length=80)
    storage_status: str | None = Field(default=None, max_length=80)
    health_status: str | None = Field(default=None, max_length=80)
    maintenance_status: str | None = Field(default=None, max_length=80)


class CameraCreate(CameraSeed):
    model_config = ConfigDict(extra="forbid")


class LocationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str | None = Field(default=None, max_length=500)
    timezone: str | None = Field(default=None, max_length=80)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def contains_a_change(self) -> LocationPatch:
        if not self.model_fields_set:
            raise ValueError("at least one location field must be supplied")
        return self


class CameraStatusPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def contains_a_change(self) -> CameraStatusPatch:
        if not self.model_fields_set:
            raise ValueError("at least one status field must be supplied")
        return self


class StreamPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stream_path: str | None = None
    hls_path: str | None = None
    stream_url: str | None = None
    hls_url: str | None = None
    selected_url: str | None = None
    delivery: str | None = Field(default=None, max_length=80)
    codec: str | None = Field(default=None, max_length=80)
    container: str | None = Field(default=None, max_length=80)
    duration_seconds: float | None = Field(default=None, ge=0)
    reachability: str | None = Field(default=None, max_length=80)
    last_checked_at: datetime | None = None

    @model_validator(mode="after")
    def contains_a_change(self) -> StreamPatch:
        if not self.model_fields_set:
            raise ValueError("at least one stream field must be supplied")
        return self


class CameraPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    location: LocationPatch | None = None
    status: CameraStatusPatch | None = None
    stream: StreamPatch | None = None
    department: str | None = Field(default=None, max_length=120)
    ownership: str | None = Field(default=None, max_length=120)
    camera_type: str | None = Field(default=None, max_length=80)
    connectivity_status: str | None = Field(default=None, max_length=80)
    storage_status: str | None = Field(default=None, max_length=80)
    health_status: str | None = Field(default=None, max_length=80)
    maintenance_status: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def contains_a_change(self) -> CameraPatch:
        if not self.model_fields_set:
            raise ValueError("at least one camera field must be supplied")
        if "display_name" in self.model_fields_set and self.display_name is None:
            raise ValueError("display_name cannot be null")
        return self


class SeedSource(BaseModel):
    model_config = ConfigDict(extra="allow")

    adapter: SourceId
    base_url: str | None = None
    safe_use: NonEmptyText
    snapshot_created_at: datetime | None = None
    snapshot_safe_use: str | None = None


class RegistrySeed(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_name: Literal["hcam.camera_registry.seed.v1"] = Field(alias="schema")
    generated_at: datetime
    source: SeedSource
    summary: dict[str, Any] = Field(default_factory=dict)
    cameras: list[CameraSeed]

    @model_validator(mode="after")
    def camera_keys_are_unique(self) -> RegistrySeed:
        camera_ids: set[str] = set()
        source_keys: set[tuple[str, str]] = set()
        for camera in self.cameras:
            if camera.camera_id in camera_ids:
                raise ValueError(f"duplicate camera_id: {camera.camera_id}")
            camera_ids.add(camera.camera_id)

            source_key = (camera.source, camera.external_id)
            if source_key in source_keys:
                raise ValueError(
                    "duplicate source/external_id: "
                    f"{camera.source}/{camera.external_id}"
                )
            source_keys.add(source_key)
        return self


class LocationResponse(BaseModel):
    label: str | None
    timezone: str | None
    latitude: float | None
    longitude: float | None


class StateResponse(BaseModel):
    metadata: str | None
    operational: str | None
    connectivity: str | None
    health: str | None
    storage: str | None
    maintenance: str | None


class StreamResponse(BaseModel):
    stream_path: str | None
    hls_path: str | None
    selected_url: str | None
    delivery: str | None
    codec: str | None
    container: str | None
    duration_seconds: float | None
    reachability: str | None
    last_checked_at: datetime | None


class ProvenanceResponse(BaseModel):
    schema_name: str
    adapter: str
    generated_at: datetime | None
    imported_at: datetime
    details: dict[str, Any]


class CameraResponse(BaseModel):
    camera_id: str
    version: int
    source: str
    external_id: str
    display_name: str
    department: str | None
    ownership: str | None
    camera_type: str | None
    location: LocationResponse
    state: StateResponse
    stream: StreamResponse
    provenance: ProvenanceResponse
    created_at: datetime
    updated_at: datetime


class CameraListResponse(BaseModel):
    items: list[CameraResponse]
    total: int
    limit: int
    offset: int


class RegistryImportResult(BaseModel):
    schema_name: str
    source: str
    created: int
    updated: int
    unchanged: int
    total: int
    audit_event_id: str
