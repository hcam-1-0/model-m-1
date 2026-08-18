from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from hcam.streams.locator import sanitize_stream_reference


_GET_STREAM_URI = b"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
 xmlns:tt="http://www.onvif.org/ver10/schema">
 <s:Body><trt:GetStreamUri><trt:StreamSetup>
  <tt:Stream>RTP-Unicast</tt:Stream>
  <tt:Transport><tt:Protocol>RTSP</tt:Protocol></tt:Transport>
 </trt:StreamSetup><trt:ProfileToken>hcam-synthetic</trt:ProfileToken>
 </trt:GetStreamUri></s:Body>
</s:Envelope>"""


class OnvifResolutionError(RuntimeError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class OnvifStreamResolver:
    timeout_seconds: float = 5.0
    max_response_bytes: int = 256 * 1024

    def resolve(self, service_url: str) -> str:
        request = Request(
            service_url,
            data=_GET_STREAM_URI,
            method="POST",
            headers={
                "Content-Type": "application/soap+xml; charset=utf-8",
                "User-Agent": "hcam-onvif-simulator-adapter/1",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read(self.max_response_bytes + 1)
        except HTTPError as exc:
            if exc.code in {401, 403}:
                raise OnvifResolutionError("unauthorized") from exc
            raise OnvifResolutionError("onvif_http_error") from exc
        except (TimeoutError, URLError, OSError) as exc:
            raise OnvifResolutionError("unreachable") from exc
        if len(payload) > self.max_response_bytes:
            raise OnvifResolutionError("onvif_response_too_large")
        try:
            root = ElementTree.fromstring(payload)
        except ElementTree.ParseError as exc:
            raise OnvifResolutionError("onvif_invalid_response") from exc
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
