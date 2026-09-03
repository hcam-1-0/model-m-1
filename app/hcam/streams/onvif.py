from __future__ import annotations

import base64
import hashlib
import os
import ssl
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Final
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
# Stdlib ElementTree is retained only for element types and ParseError.
from xml.etree import ElementTree  # nosec B405
# saxutils.escape emits escaped text; it does not parse XML.
from xml.sax.saxutils import escape  # nosec B406

import httpx
from defusedxml import ElementTree as DefusedElementTree
from defusedxml.common import DefusedXmlException

from hcam.streams.locator import sanitize_stream_reference
from hcam.streams.network import OnvifNetworkPolicy, StreamNetworkPolicyError
from hcam.streams.secrets import CameraCredentials


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
_GET_DEVICE_INFORMATION_ACTION: Final = (
    "http://www.onvif.org/ver10/device/wsdl/GetDeviceInformation"
)
_GET_SYSTEM_DATE_AND_TIME_ACTION: Final = (
    "http://www.onvif.org/ver10/device/wsdl/GetSystemDateAndTime"
)
_GET_SERVICES_ACTION: Final = "http://www.onvif.org/ver10/device/wsdl/GetServices"
_GET_DEVICE_INFORMATION_BODY: Final = (
    '<tds:GetDeviceInformation xmlns:tds="http://www.onvif.org/ver10/device/wsdl" />'
)
_GET_SYSTEM_DATE_AND_TIME_BODY: Final = (
    '<tds:GetSystemDateAndTime xmlns:tds="http://www.onvif.org/ver10/device/wsdl" />'
)
_GET_SERVICES_BODY: Final = (
    '<tds:GetServices xmlns:tds="http://www.onvif.org/ver10/device/wsdl">'
    "<tds:IncludeCapability>false</tds:IncludeCapability></tds:GetServices>"
)
_GET_SERVICE_CAPABILITIES_BODY: Final = (
    '<trt:GetServiceCapabilities xmlns:trt="http://www.onvif.org/ver10/media/wsdl" />'
)
_GET_PROFILES_BODY: Final = (
    '<trt:GetProfiles xmlns:trt="http://www.onvif.org/ver10/media/wsdl" />'
)
_MAX_PROFILES: Final = 64
_MAX_SERVICES: Final = 64
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
        return DefusedElementTree.fromstring(document)
    except (ElementTree.ParseError, DefusedXmlException) as exc:
        raise OnvifResolutionError("onvif_invalid_response") from exc


def _wsse_security_header(credentials: CameraCredentials) -> str:
    nonce = os.urandom(16)
    created = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    digest = base64.b64encode(
        hashlib.sha1(
            nonce + created.encode("utf-8") + credentials.password.encode("utf-8"),
            usedforsecurity=False,  # ONVIF UsernameToken Profile 1.0 mandates SHA-1.
        ).digest()
    ).decode("ascii")
    encoded_nonce = base64.b64encode(nonce).decode("ascii")
    username = escape(credentials.username)
    return (
        '<wsse:Security s:mustUnderstand="1" '
        'xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/'
        'oasis-200401-wss-wssecurity-secext-1.0.xsd" '
        'xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/'
        'oasis-200401-wss-wssecurity-utility-1.0.xsd">'
        "<wsse:UsernameToken><wsse:Username>"
        f"{username}</wsse:Username>"
        '<wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/'
        'oasis-200401-wss-username-token-profile-1.0#PasswordDigest">'
        f"{digest}</wsse:Password>"
        '<wsse:Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/'
        'oasis-200401-wss-soap-message-security-1.0#Base64Binary">'
        f"{encoded_nonce}</wsse:Nonce><wsu:Created>{created}</wsu:Created>"
        "</wsse:UsernameToken></wsse:Security>"
    )


def _soap_envelope(
    body: str,
    *,
    credentials: CameraCredentials | None,
    auth_mode: str,
    extra_header_xml: str = "",
) -> bytes:
    header_parts: list[str] = []
    if auth_mode in {"wsse_password_digest", "wsse_and_http_digest"}:
        if credentials is None:
            raise OnvifResolutionError("credentials_unavailable")
        header_parts.append(_wsse_security_header(credentials))
    if extra_header_xml:
        header_parts.append(extra_header_xml)
    header = f"<s:Header>{''.join(header_parts)}</s:Header>" if header_parts else ""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">'
        f"{header}<s:Body>{body}</s:Body></s:Envelope>"
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class HttpxOnvifTransport:
    timeout_seconds: float = 5.0
    max_response_bytes: int = 256 * 1024
    ca_bundle: Path | None = None
    network_policy: OnvifNetworkPolicy | None = None

    def with_network_policy(self, policy: OnvifNetworkPolicy) -> HttpxOnvifTransport:
        return replace(self, network_policy=policy)

    def request(
        self,
        service_url: str,
        payload: bytes,
        *,
        action: str,
        credentials: CameraCredentials | None,
        auth_mode: str,
    ) -> ElementTree.Element:
        auth: httpx.DigestAuth | None = None
        if auth_mode in {"http_digest", "wsse_and_http_digest"}:
            if credentials is None:
                raise OnvifResolutionError("credentials_unavailable")
            auth = httpx.DigestAuth(credentials.username, credentials.password)
        request_url = service_url
        request_headers = {
            "Content-Type": (
                'application/soap+xml; charset=utf-8; action="' + action + '"'
            ),
            "User-Agent": "hcam-onvif-adapter/2",
        }
        extensions = None
        if self.network_policy is not None:
            try:
                target = self.network_policy.authorize(service_url)
            except StreamNetworkPolicyError as exc:
                raise OnvifResolutionError("network_policy_denied") from exc
            request_url = target.request_url
            request_headers["Host"] = target.host_header
            if target.sni_hostname is not None:
                extensions = {"sni_hostname": target.sni_hostname}
        verify: ssl.SSLContext | bool = True
        if self.ca_bundle is not None:
            verify = ssl.create_default_context(cafile=str(self.ca_bundle))
        try:
            with httpx.Client(
                auth=auth,
                verify=verify,
                timeout=self.timeout_seconds,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                with client.stream(
                    "POST",
                    request_url,
                    content=payload,
                    headers=request_headers,
                    extensions=extensions,
                ) as response:
                    if response.status_code in {401, 403}:
                        raise OnvifResolutionError("unauthorized")
                    if 300 <= response.status_code < 400:
                        raise OnvifResolutionError("onvif_redirect_denied")
                    if response.status_code >= 400:
                        raise OnvifResolutionError("onvif_http_error")
                    document = bytearray()
                    for chunk in response.iter_bytes():
                        document.extend(chunk)
                        if len(document) > self.max_response_bytes:
                            raise OnvifResolutionError("onvif_response_too_large")
        except OnvifResolutionError:
            raise
        except httpx.TimeoutException as exc:
            raise OnvifResolutionError("unreachable") from exc
        except (httpx.NetworkError, ssl.SSLError, OSError) as exc:
            raise OnvifResolutionError("unreachable") from exc
        try:
            root = DefusedElementTree.fromstring(bytes(document))
        except (ElementTree.ParseError, DefusedXmlException) as exc:
            raise OnvifResolutionError("onvif_invalid_response") from exc
        if _first_descendant(root, "Fault") is not None:
            raise OnvifResolutionError("onvif_soap_fault")
        return root


@dataclass(frozen=True, slots=True)
class OnvifSoapClient:
    transport: HttpxOnvifTransport
    credentials: CameraCredentials | None = None
    auth_mode: str = "none"

    def request(
        self,
        service_url: str,
        body: str,
        *,
        action: str,
        extra_header_xml: str = "",
    ) -> ElementTree.Element:
        payload = _soap_envelope(
            body,
            credentials=self.credentials,
            auth_mode=self.auth_mode,
            extra_header_xml=extra_header_xml,
        )
        return self.transport.request(
            service_url,
            payload,
            action=action,
            credentials=self.credentials,
            auth_mode=self.auth_mode,
        )


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
    video_source_token: str | None = None


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


@dataclass(frozen=True, slots=True)
class OnvifDeviceInformation:
    manufacturer: str | None
    model: str | None
    firmware_version: str | None
    serial_number: str | None
    hardware_id: str | None


@dataclass(frozen=True, slots=True)
class OnvifService:
    namespace: str
    xaddr: str
    version: str | None


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
        video_source = _first_descendant(profile, "VideoSourceConfiguration")
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
                video_source_token=_bounded_text(
                    _first_descendant(video_source, "SourceToken")
                    if video_source is not None
                    else None
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


def parse_device_information(root: ElementTree.Element) -> OnvifDeviceInformation:
    return OnvifDeviceInformation(
        manufacturer=_bounded_text(_first_descendant(root, "Manufacturer")),
        model=_bounded_text(_first_descendant(root, "Model")),
        firmware_version=_bounded_text(_first_descendant(root, "FirmwareVersion")),
        serial_number=_bounded_text(_first_descendant(root, "SerialNumber")),
        hardware_id=_bounded_text(_first_descendant(root, "HardwareId")),
    )


def parse_services(root: ElementTree.Element) -> tuple[OnvifService, ...]:
    elements = [item for item in root.iter() if _local_name(item) == "Service"]
    if len(elements) > _MAX_SERVICES:
        raise OnvifResolutionError("onvif_too_many_services")
    services: list[OnvifService] = []
    for element in elements:
        namespace = _bounded_text(_first_descendant(element, "Namespace"))
        xaddr = _bounded_text(_first_descendant(element, "XAddr"))
        if namespace is None or xaddr is None:
            raise OnvifResolutionError("onvif_invalid_services")
        version_element = _first_descendant(element, "Version")
        major = _bounded_text(
            _first_descendant(version_element, "Major")
            if version_element is not None
            else None
        )
        minor = _bounded_text(
            _first_descendant(version_element, "Minor")
            if version_element is not None
            else None
        )
        if major is not None and not major.isdigit():
            raise OnvifResolutionError("onvif_invalid_services")
        if minor is not None and not minor.isdigit():
            raise OnvifResolutionError("onvif_invalid_services")
        services.append(
            OnvifService(
                namespace=namespace,
                xaddr=xaddr,
                version=f"{major}.{minor}" if major and minor else major,
            )
        )
    return tuple(services)


def parse_device_clock_offset(
    root: ElementTree.Element,
    *,
    observed_at: datetime,
) -> float:
    utc_element = _first_descendant(root, "UTCDateTime")
    if utc_element is None:
        raise OnvifResolutionError("onvif_invalid_device_time")
    time_element = _first_descendant(utc_element, "Time")
    date_element = _first_descendant(utc_element, "Date")
    try:
        device_time = datetime(
            int(_bounded_text(_first_descendant(date_element, "Year")) or ""),
            int(_bounded_text(_first_descendant(date_element, "Month")) or ""),
            int(_bounded_text(_first_descendant(date_element, "Day")) or ""),
            int(_bounded_text(_first_descendant(time_element, "Hour")) or ""),
            int(_bounded_text(_first_descendant(time_element, "Minute")) or ""),
            int(_bounded_text(_first_descendant(time_element, "Second")) or ""),
            tzinfo=UTC,
        )
    except (TypeError, ValueError) as exc:
        raise OnvifResolutionError("onvif_invalid_device_time") from exc
    return (device_time - observed_at.astimezone(UTC)).total_seconds()


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
    soap_client: OnvifSoapClient | None = None

    def discover(self, service_url: str) -> OnvifMediaCapabilities:
        if self.soap_client is not None:
            capability_root = self.soap_client.request(
                service_url,
                _GET_SERVICE_CAPABILITIES_BODY,
                action=_GET_SERVICE_CAPABILITIES_ACTION,
            )
            profile_root = self.soap_client.request(
                service_url,
                _GET_PROFILES_BODY,
                action=_GET_PROFILES_ACTION,
            )
        else:
            capability_root = _soap_request(
                service_url,
                _GET_SERVICE_CAPABILITIES,
                action=_GET_SERVICE_CAPABILITIES_ACTION,
                timeout_seconds=self.timeout_seconds,
                max_response_bytes=self.max_response_bytes,
            )
            profile_root = _soap_request(
                service_url,
                _GET_PROFILES,
                action=_GET_PROFILES_ACTION,
                timeout_seconds=self.timeout_seconds,
                max_response_bytes=self.max_response_bytes,
            )
        values = _parse_service_capabilities(
            capability_root
        )
        return OnvifMediaCapabilities(
            **values,
            profiles=_parse_profiles(profile_root),
        )


def get_device_information(
    client: OnvifSoapClient,
    service_url: str,
) -> OnvifDeviceInformation:
    return parse_device_information(
        client.request(
            service_url,
            _GET_DEVICE_INFORMATION_BODY,
            action=_GET_DEVICE_INFORMATION_ACTION,
        )
    )


def get_services(
    client: OnvifSoapClient,
    service_url: str,
) -> tuple[OnvifService, ...]:
    return parse_services(
        client.request(
            service_url,
            _GET_SERVICES_BODY,
            action=_GET_SERVICES_ACTION,
        )
    )


def get_profiles(
    client: OnvifSoapClient,
    service_url: str,
) -> tuple[OnvifMediaProfile, ...]:
    return _parse_profiles(
        client.request(
            service_url,
            _GET_PROFILES_BODY,
            action=_GET_PROFILES_ACTION,
        )
    )


def get_device_clock_offset(
    client: OnvifSoapClient,
    service_url: str,
    *,
    observed_at: datetime,
) -> float:
    return parse_device_clock_offset(
        client.request(
            service_url,
            _GET_SYSTEM_DATE_AND_TIME_BODY,
            action=_GET_SYSTEM_DATE_AND_TIME_ACTION,
        ),
        observed_at=observed_at,
    )
