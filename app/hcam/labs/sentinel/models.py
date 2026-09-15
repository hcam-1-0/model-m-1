from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from urllib.parse import urljoin, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field


SENTINEL_CATALOG_CONTRACT = "sentinel_sandbox_catalog_v1"
SENTINEL_CATALOG_SCHEMA_VERSION = 1
SUPPORTED_SENTINEL_CATALOG_SCHEMA_VERSIONS = frozenset({1})

# These values are intentionally stable: they are suitable for safe diagnostics
# and bounded metrics, but never include an upstream value or locator.
CONTRACT_ERROR_CODES = frozenset(
    {
        "schema_version_unsupported",
        "schema_drift",
        "required_field_missing",
        "invalid_field_type",
        "invalid_identifier",
        "duplicate_identifier",
        "unsafe_locator",
        "invalid_transport",
        "transport_missing",
        "invalid_geometry",
        "invalid_timestamp",
        "stale_catalogue",
        "out_of_order_record",
        "over_capacity",
        "ambiguous_payload",
    }
)


class CatalogValidationError(ValueError):
    """A catalogue failed a bounded, safe validation rule."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


TransportRole = Literal["inference", "preview", "fallback"]
Protocol = Literal["rtsp", "http", "https"]


@dataclass(frozen=True, slots=True)
class NetworkRule:
    scheme: Protocol
    host: str
    port: int
    path_prefix: str


class ExactNetworkPolicy:
    """Exact generated-lab destination rules; no DNS or wildcard expansion."""

    def __init__(self, rules: tuple[NetworkRule, ...]) -> None:
        if not rules:
            raise ValueError("at least one exact network rule is required")
        self._rules = rules

    def validate(
        self,
        raw_locator: str,
        *,
        origin: str,
        role: TransportRole,
    ) -> "CatalogEndpoint":
        if not isinstance(raw_locator, str) or not raw_locator.strip():
            raise CatalogValidationError("invalid_transport_url")
        locator = raw_locator.strip()
        if locator.startswith("/"):
            if role != "fallback":
                raise CatalogValidationError("relative_url_not_allowed")
            locator = urljoin(origin, locator)
        parsed = urlsplit(locator)
        scheme = parsed.scheme.lower()
        host = (parsed.hostname or "").lower()
        if scheme not in {"rtsp", "http", "https"} or not host:
            raise CatalogValidationError("unsupported_transport_destination")
        if parsed.username is not None or parsed.password is not None:
            raise CatalogValidationError("credential_bearing_url")
        if parsed.query or parsed.fragment:
            raise CatalogValidationError("secret_bearing_url_component")
        try:
            port = parsed.port
        except ValueError as exc:
            raise CatalogValidationError("invalid_transport_port") from exc
        port = port or {"rtsp": 554, "http": 80, "https": 443}[scheme]
        path = parsed.path or "/"
        rule = next(
            (
                item
                for item in self._rules
                if item.scheme == scheme
                and item.host.lower() == host
                and item.port == port
                and path.startswith(item.path_prefix)
            ),
            None,
        )
        if rule is None:
            raise CatalogValidationError("network_policy_denied")
        netloc = (
            host
            if port == {"rtsp": 554, "http": 80, "https": 443}[scheme]
            else f"{host}:{port}"
        )
        normalized = urlunsplit((scheme, netloc, path, "", ""))
        return CatalogEndpoint(role=role, protocol=scheme, locator=normalized)


class CatalogEndpoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: TransportRole
    protocol: Protocol
    locator: str = Field(min_length=1, max_length=2048)

    @property
    def locator_sha256(self) -> str:
        return hashlib.sha256(self.locator.encode("utf-8")).hexdigest()

    def canonical(self) -> dict[str, str]:
        return {
            "locator_sha256": self.locator_sha256,
            "protocol": self.protocol,
            "role": self.role,
        }


class CatalogCamera(BaseModel):
    model_config = ConfigDict(frozen=True)

    external_id: str = Field(min_length=1, max_length=160)
    number: int | None = None
    name: str | None = Field(default=None, max_length=240)
    location: str | None = Field(default=None, max_length=500)
    advertised_live: bool
    advertised_codec: Literal["h264", "hevc"] | None = None
    width: int | None = Field(default=None, le=16384)
    height: int | None = Field(default=None, le=16384)
    fps: float | None = Field(default=None, le=240)
    bitrate_kbps: int | None = Field(default=None, le=1_000_000)
    bits_per_pixel: float | None = Field(default=None, le=64)
    profile_id: str | None = Field(default=None, max_length=80)
    capacity_holder: bool = False
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    source_provider: str | None = Field(default=None, max_length=80)
    department: str | None = Field(default=None, max_length=80)
    camera_type: str | None = Field(default=None, max_length=80)
    catalog_updated_at: datetime | None = None
    endpoints: tuple[CatalogEndpoint, ...]
    warning_codes: tuple[str, ...] = ()

    def canonical(self) -> dict[str, object]:
        return {
            "advertised_codec": self.advertised_codec,
            "advertised_live": self.advertised_live,
            "bitrate_kbps": self.bitrate_kbps,
            "bits_per_pixel": self.bits_per_pixel,
            "capacity_holder": self.capacity_holder,
            "camera_type": self.camera_type,
            "catalog_updated_at": (
                self.catalog_updated_at.astimezone(UTC).isoformat().replace("+00:00", "Z")
                if self.catalog_updated_at is not None
                else None
            ),
            "department": self.department,
            "endpoints": [endpoint.canonical() for endpoint in self.endpoints],
            "external_id": self.external_id,
            "fps": self.fps,
            "height": self.height,
            "location": self.location,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "name": self.name,
            "number": self.number,
            "profile_id": self.profile_id,
            "source_provider": self.source_provider,
            "width": self.width,
        }

    def browser_safe(self) -> dict[str, object]:
        """Explicit browser DTO allowlist; endpoints and source locators stay internal."""
        return {
            "id": self.external_id,
            "name": self.name,
            "advertised_live": self.advertised_live,
            "advertised_codec": self.advertised_codec,
            "profile_id": self.profile_id,
            "preview_compatible": any(endpoint.role == "preview" for endpoint in self.endpoints),
            "registry_state": "catalogued",
        }

    def gis_safe(self) -> dict[str, object]:
        """Explicit GIS DTO allowlist. Geometry is display-only and never a locator."""
        return {
            "id": self.external_id,
            "name": self.name,
            "department": self.department,
            "camera_type": self.camera_type,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "advertised_live": self.advertised_live,
            "registry_state": "catalogued",
            "preview_compatible": any(endpoint.role == "preview" for endpoint in self.endpoints),
        }

    def endpoint_document(self) -> list[dict[str, str]]:
        return [endpoint.model_dump(mode="json") for endpoint in self.endpoints]


class NormalizedCatalog(BaseModel):
    model_config = ConfigDict(frozen=True)

    cameras: tuple[CatalogCamera, ...]
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    canonical_json: str
    warning_count: int = Field(ge=0)


_KNOWN_CAMERA_FIELDS = {
    "id",
    "number",
    "name",
    "location",
    "codec",
    "live",
    "width",
    "height",
    "fps",
    "bitrate_kbps",
    "bits_per_pixel",
    "rtsp_url",
    "webrtc_url",
    "hls_live_url",
    "lab_profile",
    "capacity_holder",
    "source_provider",
    "department",
    "camera_type",
    "longitude",
    "latitude",
    "updated_at",
    "transports",
    "tombstone",
}


def _contract_version(document: dict[str, object]) -> None:
    """Validate the explicit v1 envelope without accepting an ambiguous version."""
    # The legacy generated-lab envelope carried only `schema`; it remains a
    # bounded v1 compatibility form. New publishers must include `contract`.
    name = document.get("contract")
    if name is None and "schema" in document:
        name = SENTINEL_CATALOG_CONTRACT
    version = document.get("schema_version", document.get("schema"))
    if name != SENTINEL_CATALOG_CONTRACT:
        raise CatalogValidationError("schema_drift")
    if isinstance(version, bool) or not isinstance(version, int):
        raise CatalogValidationError("schema_version_unsupported")
    if version not in SUPPORTED_SENTINEL_CATALOG_SCHEMA_VERSIONS:
        raise CatalogValidationError("schema_version_unsupported")


def _coordinate(value: Any, *, minimum: float, maximum: float) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CatalogValidationError("invalid_geometry")
    normalized = float(value)
    if not math.isfinite(normalized) or not minimum <= normalized <= maximum:
        raise CatalogValidationError("invalid_geometry")
    return normalized


def _timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > 64:
        raise CatalogValidationError("invalid_timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CatalogValidationError("invalid_timestamp") from exc
    if parsed.tzinfo is None:
        raise CatalogValidationError("invalid_timestamp")
    normalized = parsed.astimezone(UTC)
    if normalized > datetime.now(UTC) + timedelta(minutes=5):
        raise CatalogValidationError("invalid_timestamp")
    return normalized


def _transport_values(raw: dict[str, Any]) -> tuple[tuple[str, TransportRole], ...]:
    """Accept legacy three-url records or an unambiguous typed transport list."""
    legacy = (("rtsp_url", "inference"), ("webrtc_url", "preview"), ("hls_live_url", "fallback"))
    if "transports" not in raw:
        return legacy
    transports = raw["transports"]
    if any(raw.get(field) not in {None, ""} for field, _ in legacy):
        raise CatalogValidationError("ambiguous_payload")
    if not isinstance(transports, list):
        raise CatalogValidationError("invalid_transport")
    values: list[tuple[str, TransportRole]] = []
    roles: set[TransportRole] = set()
    protocol_roles: dict[str, TransportRole] = {
        "rtsp": "inference", "rtsp_tcp": "inference", "whep": "preview",
        "webrtc": "preview", "hls": "fallback",
    }
    for item in transports:
        if not isinstance(item, dict) or set(item) - {"kind", "url"}:
            raise CatalogValidationError("invalid_transport")
        kind, value = item.get("kind"), item.get("url")
        if not isinstance(kind, str) or kind.strip().lower() not in protocol_roles:
            raise CatalogValidationError("invalid_transport")
        if not isinstance(value, str):
            raise CatalogValidationError("invalid_transport")
        role = protocol_roles[kind.strip().lower()]
        if role in roles:
            raise CatalogValidationError("ambiguous_payload")
        roles.add(role)
        values.append((value, role))
    return tuple(values)


def _text(value: Any, *, code: str, maximum: int, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise CatalogValidationError(code)
    normalized = str(value).strip()
    if (required and not normalized) or len(normalized) > maximum:
        raise CatalogValidationError(code)
    if any(unicodedata.category(character).startswith("C") for character in normalized):
        raise CatalogValidationError(code)
    return normalized or None


def _number(
    value: Any,
    *,
    integral: bool,
    maximum: float,
) -> tuple[int | float | None, bool]:
    if value is None:
        return None, False
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, True
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0 or numeric > maximum:
        return None, True
    if integral:
        if not numeric.is_integer():
            return None, True
        return int(numeric), False
    return numeric, False


def _codec(value: Any) -> tuple[Literal["h264", "hevc"] | None, bool]:
    if value is None or value == "":
        return None, False
    if not isinstance(value, str):
        return None, True
    compact = value.strip().lower().replace(".", "").replace("-", "")
    if compact in {"h264", "avc", "avc1"}:
        return "h264", False
    if compact in {"h265", "hevc", "hev1", "hvc1"}:
        return "hevc", False
    return None, True


def normalize_catalog_document(
    document: object,
    *,
    origin: str,
    network_policy: ExactNetworkPolicy,
    max_records: int = 500,
) -> NormalizedCatalog:
    if not isinstance(document, dict):
        raise CatalogValidationError("invalid_field_type")
    if "cameras" not in document:
        raise CatalogValidationError("required_field_missing")
    if not isinstance(document["cameras"], list):
        raise CatalogValidationError("invalid_field_type")
    _contract_version(document)
    raw_cameras = document["cameras"]
    if len(raw_cameras) > max_records:
        raise CatalogValidationError("over_capacity")
    cameras: list[CatalogCamera] = []
    seen: set[str] = set()
    for raw in raw_cameras:
        if not isinstance(raw, dict):
            raise CatalogValidationError("invalid_field_type")
        if "id" not in raw:
            raise CatalogValidationError("required_field_missing")
        external_id = _text(raw.get("id"), code="invalid_identifier", maximum=160, required=True)
        assert external_id is not None
        if external_id in seen:
            raise CatalogValidationError("duplicate_identifier")
        seen.add(external_id)
        if "live" not in raw:
            raise CatalogValidationError("required_field_missing")
        live = raw.get("live")
        if not isinstance(live, bool):
            raise CatalogValidationError("invalid_field_type")
        warnings: set[str] = set()
        unknown = set(raw) - _KNOWN_CAMERA_FIELDS
        if unknown:
            warnings.add("unknown_camera_fields")
        codec, codec_warning = _codec(raw.get("codec"))
        if codec_warning:
            warnings.add("unknown_codec")
        width, invalid = _number(raw.get("width"), integral=True, maximum=16384)
        if invalid:
            warnings.add("unknown_width")
        height, invalid = _number(raw.get("height"), integral=True, maximum=16384)
        if invalid:
            warnings.add("unknown_height")
        fps, invalid = _number(raw.get("fps"), integral=False, maximum=240)
        if invalid:
            warnings.add("unknown_fps")
        bitrate, invalid = _number(
            raw.get("bitrate_kbps"), integral=True, maximum=1_000_000
        )
        if invalid:
            warnings.add("unknown_bitrate")
        bpp, invalid = _number(raw.get("bits_per_pixel"), integral=False, maximum=64)
        if invalid:
            warnings.add("unknown_bits_per_pixel")
        number, invalid = _number(raw.get("number"), integral=True, maximum=10_000_000)
        if invalid:
            warnings.add("unknown_number")
        endpoints: list[CatalogEndpoint] = []
        for field, role in _transport_values(raw):
            value = (
                raw.get(field)
                if field in {"rtsp_url", "webrtc_url", "hls_live_url"}
                else field
            )
            if value in {None, ""}:
                continue
            try:
                endpoints.append(
                    network_policy.validate(value, origin=origin, role=role)  # type: ignore[arg-type]
                )
            except CatalogValidationError as exc:
                raise CatalogValidationError("unsafe_locator") from exc
        if not endpoints:
            raise CatalogValidationError("transport_missing")
        profile = _text(raw.get("lab_profile"), code="invalid_profile_id", maximum=80)
        capacity_holder = raw.get("capacity_holder", False)
        if not isinstance(capacity_holder, bool):
            raise CatalogValidationError("invalid_capacity_holder")
        longitude = _coordinate(raw.get("longitude"), minimum=-180, maximum=180)
        latitude = _coordinate(raw.get("latitude"), minimum=-90, maximum=90)
        if (longitude is None) != (latitude is None):
            raise CatalogValidationError("invalid_geometry")
        if longitude is not None and latitude is not None and abs(longitude) <= 90 and abs(latitude) > 90:
            raise CatalogValidationError("ambiguous_payload")
        cameras.append(
            CatalogCamera(
                external_id=external_id,
                number=number if isinstance(number, int) else None,
                name=_text(raw.get("name"), code="invalid_camera_name", maximum=240),
                location=_text(
                    raw.get("location"), code="invalid_location", maximum=500
                ),
                advertised_live=live,
                advertised_codec=codec,
                width=width if isinstance(width, int) else None,
                height=height if isinstance(height, int) else None,
                fps=float(fps) if fps is not None else None,
                bitrate_kbps=bitrate if isinstance(bitrate, int) else None,
                bits_per_pixel=float(bpp) if bpp is not None else None,
                profile_id=profile,
                capacity_holder=capacity_holder,
                longitude=longitude,
                latitude=latitude,
                source_provider=_text(raw.get("source_provider"), code="invalid_field_type", maximum=80),
                department=_text(raw.get("department"), code="invalid_field_type", maximum=80),
                camera_type=_text(raw.get("camera_type"), code="invalid_field_type", maximum=80),
                catalog_updated_at=_timestamp(raw.get("updated_at")),
                endpoints=tuple(sorted(endpoints, key=lambda item: item.role)),
                warning_codes=tuple(sorted(warnings)),
            )
        )
    cameras.sort(key=lambda item: item.external_id)
    canonical = {"cameras": [camera.canonical() for camera in cameras]}
    canonical_json = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return NormalizedCatalog(
        cameras=tuple(cameras),
        fingerprint=hashlib.sha256(canonical_json.encode("ascii")).hexdigest(),
        canonical_json=canonical_json,
        warning_count=sum(len(camera.warning_codes) for camera in cameras),
    )
