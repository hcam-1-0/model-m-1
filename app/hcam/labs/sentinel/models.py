from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urljoin, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field


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
    endpoints: tuple[CatalogEndpoint, ...]
    warning_codes: tuple[str, ...] = ()

    def canonical(self) -> dict[str, object]:
        return {
            "advertised_codec": self.advertised_codec,
            "advertised_live": self.advertised_live,
            "bitrate_kbps": self.bitrate_kbps,
            "bits_per_pixel": self.bits_per_pixel,
            "capacity_holder": self.capacity_holder,
            "endpoints": [endpoint.canonical() for endpoint in self.endpoints],
            "external_id": self.external_id,
            "fps": self.fps,
            "height": self.height,
            "location": self.location,
            "name": self.name,
            "number": self.number,
            "profile_id": self.profile_id,
            "width": self.width,
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
}


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
    if not isinstance(document, dict) or not isinstance(document.get("cameras"), list):
        raise CatalogValidationError("invalid_catalog_root")
    raw_cameras = document["cameras"]
    if len(raw_cameras) > max_records:
        raise CatalogValidationError("catalog_record_limit_exceeded")
    cameras: list[CatalogCamera] = []
    seen: set[str] = set()
    for raw in raw_cameras:
        if not isinstance(raw, dict):
            raise CatalogValidationError("invalid_camera_record")
        external_id = _text(
            raw.get("id"), code="invalid_camera_id", maximum=160, required=True
        )
        assert external_id is not None
        if external_id in seen:
            raise CatalogValidationError("duplicate_camera_id")
        seen.add(external_id)
        live = raw.get("live")
        if not isinstance(live, bool):
            raise CatalogValidationError("invalid_live_state")
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
        for field, role in (
            ("rtsp_url", "inference"),
            ("webrtc_url", "preview"),
            ("hls_live_url", "fallback"),
        ):
            value = raw.get(field)
            if value in {None, ""}:
                continue
            endpoints.append(
                network_policy.validate(value, origin=origin, role=role)  # type: ignore[arg-type]
            )
        if not endpoints:
            raise CatalogValidationError("camera_has_no_approved_transport")
        profile = _text(raw.get("lab_profile"), code="invalid_profile_id", maximum=80)
        capacity_holder = raw.get("capacity_holder", False)
        if not isinstance(capacity_holder, bool):
            raise CatalogValidationError("invalid_capacity_holder")
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
