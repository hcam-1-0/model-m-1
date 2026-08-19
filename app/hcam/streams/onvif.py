from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from xml.etree import ElementTree

from hcam.streams.locator import sanitize_stream_reference


_GET_STREAM_URI: Final = b"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
 xmlns:tt="http://www.onvif.org/ver10/schema">
 <s:Body><trt:GetStreamUri><trt:StreamSetup>
  <tt:Stream>RTP-Unicast</tt:Stream>
  <tt:Transport><tt:Protocol>RTSP</tt:Protocol></tt:Transport>
 </trt:StreamSetup><trt:ProfileToken>hcam-synthetic</trt:ProfileToken>
 </trt:GetStreamUri></s:Body>
</s:Envelope>"""
_GET_SERVICE_CAPABILITIES: Final = b"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
 <s:Body><trt:GetServiceCapabilities /></s:Body>
</s:Envelope>"""
_GET_PROFILES: Final = b"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
 <s:Body><trt:GetProfiles /></s:Body>
</s:Envelope>"""
_GET_STREAM_URI_ACTION: Final = (
    "http://www.onvif.org/ver10/media/wsdl/GetStreamUri"
)
_GET_SERVICE_CAPABILITIES_ACTION: Final = (
    "http://www.onvif.org/ver10/media/wsdl/GetServiceCapabilities"
)
_GET_PROFILES_ACTION: Final = "http://www.onvif.org/ver10/media/wsdl/GetProfiles"
_MAX_PROFILES: Final = 64
_MAX_TEXT_LENGTH: Final = 255


class OnvifResolutionError(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self, _request, response, code, _message, headers, new_url
    ):
        raise HTTPError(new_url, code, "ONVIF redirects are denied", headers, response)


def _open_request(request: Request, *, timeout: float):
    opener = build_opener(ProxyHandler({}), _NoRedirectHandler())
    return opener.open(request, timeout=timeout)


def _soap_request(
    service_url: str,
    payload: bytes,
    *,
    action: str,
    timeout_seconds: float,
    max_response_bytes: int,
) -> ElementTree.Element:
    request = Request(
        service_url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": (
                'application/soap+xml; charset=utf-8; action="' + action + '"'
            ),
            "User-Agent": "hcam-onvif-adapter/1",
        },
    )
    try:
        with _open_request(request, timeout=timeout_seconds) as response:
            document = response.read(max_response_bytes + 1)
    except HTTPError as exc:
        if exc.code in {401, 403}:
            raise OnvifResolutionError("unauthorized") from exc
        if 300 <= exc.code < 400:
            raise OnvifResolutionError("onvif_redirect_denied") from exc
        raise OnvifResolutionError("onvif_http_error") from exc
    except (TimeoutError, URLError, OSError) as exc:
        raise OnvifResolutionError("unreachable") from exc
    if len(document) > max_response_bytes:
        raise OnvifResolutionError("onvif_response_too_large")
    try:
        return ElementTree.fromstring(document)
    except ElementTree.ParseError as exc:
        raise OnvifResolutionError("onvif_invalid_response") from exc


def _local_name(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _first_descendant(
    element: ElementTree.Element, local_name: str
) -> ElementTree.Element | None:
    return next(
        (candidate for candidate in element.iter() if _local_name(candidate) == local_name),
        None,
    )


def _bounded_text(
    element: ElementTree.Element | None,
) -> str | None:
    value = (element.text or "").strip() if element is not None else ""
    if len(value) > _MAX_TEXT_LENGTH:
        raise OnvifResolutionError("onvif_invalid_capabilities")
    return value or None


def _optional_boolean(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1"}:
        return True
    if normalized in {"false", "0"}:
        return False
    raise OnvifResolutionError("onvif_invalid_capabilities")


def _optional_positive_integer(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise OnvifResolutionError("onvif_invalid_capabilities") from exc
    if not 1 <= parsed <= 1_000_000:
        raise OnvifResolutionError("onvif_invalid_capabilities")
    return parsed


@dataclass(frozen=True, slots=True)
class OnvifMediaProfile:
    token: str
    name: str | None
    fixed: bool | None
    video_encoding: str | None
    width: int | None
    height: int | None
    frame_rate_limit: int | None
    audio_encoding: str | None
    ptz_configured: bool
    analytics_configured: bool
    metadata_configured: bool


@dataclass(frozen=True, slots=True)
class OnvifMediaCapabilities:
    snapshot_uri: bool | None
    rotation: bool | None
    video_source_mode: bool | None
    osd: bool | None
    temporary_osd_text: bool | None
    exi_compression: bool | None
    maximum_profiles: int | None
    profiles: tuple[OnvifMediaProfile, ...]


def _parse_service_capabilities(root: ElementTree.Element) -> dict[str, object]:
    capabilities = _first_descendant(root, "Capabilities")
    if capabilities is None:
        raise OnvifResolutionError("onvif_invalid_capabilities")
    maximum = capabilities.attrib.get("MaximumNumberOfProfiles")
    if maximum is None:
        maximum_element = _first_descendant(capabilities, "MaximumNumberOfProfiles")
        maximum = _bounded_text(maximum_element)
    return {
        "snapshot_uri": _optional_boolean(capabilities.attrib.get("SnapshotUri")),
        "rotation": _optional_boolean(capabilities.attrib.get("Rotation")),
        "video_source_mode": _optional_boolean(
            capabilities.attrib.get("VideoSourceMode")
        ),
        "osd": _optional_boolean(capabilities.attrib.get("OSD")),
        "temporary_osd_text": _optional_boolean(
            capabilities.attrib.get("TemporaryOSDText")
        ),
        "exi_compression": _optional_boolean(
            capabilities.attrib.get("EXICompression")
        ),
        "maximum_profiles": _optional_positive_integer(maximum),
    }


def _parse_profiles(root: ElementTree.Element) -> tuple[OnvifMediaProfile, ...]:
    profile_elements = [
        element for element in root.iter() if _local_name(element) == "Profiles"
    ]
    if len(profile_elements) > _MAX_PROFILES:
        raise OnvifResolutionError("onvif_too_many_profiles")
    profiles: list[OnvifMediaProfile] = []
    for profile in profile_elements:
        token = profile.attrib.get("token", "").strip()
        if not token or len(token) > _MAX_TEXT_LENGTH:
            raise OnvifResolutionError("onvif_invalid_capabilities")
        video = _first_descendant(profile, "VideoEncoderConfiguration")
        resolution = _first_descendant(video, "Resolution") if video is not None else None
        rate_control = (
            _first_descendant(video, "RateControl") if video is not None else None
        )
        audio = _first_descendant(profile, "AudioEncoderConfiguration")
        profiles.append(
            OnvifMediaProfile(
                token=token,
                name=_bounded_text(_first_descendant(profile, "Name")),
                fixed=_optional_boolean(profile.attrib.get("fixed")),
                video_encoding=_bounded_text(
                    _first_descendant(video, "Encoding") if video is not None else None
                ),
                width=_optional_positive_integer(
                    _bounded_text(
                        _first_descendant(resolution, "Width")
                        if resolution is not None
                        else None
                    )
                ),
                height=_optional_positive_integer(
                    _bounded_text(
                        _first_descendant(resolution, "Height")
                        if resolution is not None
                        else None
                    )
                ),
                frame_rate_limit=_optional_positive_integer(
                    _bounded_text(
                        _first_descendant(rate_control, "FrameRateLimit")
                        if rate_control is not None
                        else None
                    )
                ),
                audio_encoding=_bounded_text(
                    _first_descendant(audio, "Encoding") if audio is not None else None
                ),
                ptz_configured=_first_descendant(profile, "PTZConfiguration")
                is not None,
                analytics_configured=_first_descendant(
                    profile, "VideoAnalyticsConfiguration"
                )
                is not None,
                metadata_configured=_first_descendant(profile, "MetadataConfiguration")
                is not None,
            )
        )
    return tuple(profiles)


@dataclass(frozen=True, slots=True)
class OnvifStreamResolver:
    timeout_seconds: float = 5.0
    max_response_bytes: int = 256 * 1024

    def resolve(self, service_url: str) -> str:
        root = _soap_request(
            service_url,
            _GET_STREAM_URI,
            action=_GET_STREAM_URI_ACTION,
            timeout_seconds=self.timeout_seconds,
            max_response_bytes=self.max_response_bytes,
        )
        uri = next(
            (
                (element.text or "").strip()
                for element in root.iter()
                if element.tag.rsplit("}", 1)[-1] == "Uri"
                and (element.text or "").strip()
            ),
            "",
        )
        sanitized = sanitize_stream_reference(uri)
        if (
            not sanitized
            or sanitized != uri
            or not sanitized.lower().startswith(("rtsp://", "rtsps://"))
        ):
            raise OnvifResolutionError("onvif_invalid_stream_uri")
        return sanitized


@dataclass(frozen=True, slots=True)
class OnvifCapabilityDiscovery:
    timeout_seconds: float = 5.0
    max_response_bytes: int = 256 * 1024

    def discover(self, service_url: str) -> OnvifMediaCapabilities:
        values = _parse_service_capabilities(
            _soap_request(
                service_url,
                _GET_SERVICE_CAPABILITIES,
                action=_GET_SERVICE_CAPABILITIES_ACTION,
                timeout_seconds=self.timeout_seconds,
                max_response_bytes=self.max_response_bytes,
            )
        )
        profile_root = _soap_request(
            service_url,
            _GET_PROFILES,
            action=_GET_PROFILES_ACTION,
            timeout_seconds=self.timeout_seconds,
            max_response_bytes=self.max_response_bytes,
        )
        return OnvifMediaCapabilities(
            **values,
            profiles=_parse_profiles(profile_root),
        )
