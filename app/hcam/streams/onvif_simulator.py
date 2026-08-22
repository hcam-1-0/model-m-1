from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
from collections.abc import Sequence
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlsplit
from urllib.request import parse_http_list, parse_keqv_list
from xml.etree import ElementTree
from xml.sax.saxutils import escape

from hcam.streams.locator import sanitize_stream_reference


def _stream_uri_response(stream_uri: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
 xmlns:tt="http://www.onvif.org/ver10/schema">
 <s:Body><trt:GetStreamUriResponse><trt:MediaUri>
  <tt:Uri>{escape(stream_uri)}</tt:Uri>
  <tt:InvalidAfterConnect>false</tt:InvalidAfterConnect>
  <tt:InvalidAfterReboot>false</tt:InvalidAfterReboot>
  <tt:Timeout>PT60S</tt:Timeout>
 </trt:MediaUri></trt:GetStreamUriResponse></s:Body>
</s:Envelope>""".encode("utf-8")


def _service_capabilities_response() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
 xmlns:tt="http://www.onvif.org/ver10/schema">
 <s:Body><trt:GetServiceCapabilitiesResponse>
  <trt:Capabilities SnapshotUri="true" Rotation="true"
   VideoSourceMode="false" OSD="true" TemporaryOSDText="false"
   EXICompression="false">
   <tt:ProfileCapabilities>
    <tt:MaximumNumberOfProfiles>8</tt:MaximumNumberOfProfiles>
   </tt:ProfileCapabilities>
  </trt:Capabilities>
 </trt:GetServiceCapabilitiesResponse></s:Body>
</s:Envelope>"""


def _profiles_response() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:trt="http://www.onvif.org/ver10/media/wsdl"
 xmlns:tt="http://www.onvif.org/ver10/schema">
 <s:Body><trt:GetProfilesResponse>
  <trt:Profiles token="hcam-main" fixed="true">
   <tt:Name>Main</tt:Name>
   <tt:VideoSourceConfiguration token="source-config-main">
    <tt:Name>Main source</tt:Name><tt:UseCount>1</tt:UseCount>
    <tt:SourceToken>source-main</tt:SourceToken>
   </tt:VideoSourceConfiguration>
   <tt:VideoEncoderConfiguration token="video-main">
    <tt:Name>Main H264</tt:Name><tt:UseCount>1</tt:UseCount>
    <tt:Encoding>H264</tt:Encoding>
    <tt:Resolution><tt:Width>1920</tt:Width><tt:Height>1080</tt:Height></tt:Resolution>
    <tt:Quality>4</tt:Quality>
    <tt:RateControl><tt:FrameRateLimit>25</tt:FrameRateLimit>
     <tt:EncodingInterval>1</tt:EncodingInterval><tt:BitrateLimit>4096</tt:BitrateLimit>
    </tt:RateControl>
   </tt:VideoEncoderConfiguration>
   <tt:AudioEncoderConfiguration token="audio-main">
    <tt:Name>Main AAC</tt:Name><tt:UseCount>1</tt:UseCount>
    <tt:Encoding>AAC</tt:Encoding>
   </tt:AudioEncoderConfiguration>
   <tt:PTZConfiguration token="ptz-main" />
   <tt:VideoAnalyticsConfiguration token="analytics-main" />
   <tt:MetadataConfiguration token="metadata-main" />
  </trt:Profiles>
  <trt:Profiles token="hcam-sub" fixed="true">
   <tt:Name>Sub</tt:Name>
   <tt:VideoSourceConfiguration token="source-config-sub">
    <tt:Name>Sub source</tt:Name><tt:UseCount>1</tt:UseCount>
    <tt:SourceToken>source-sub</tt:SourceToken>
   </tt:VideoSourceConfiguration>
   <tt:VideoEncoderConfiguration token="video-sub">
    <tt:Name>Sub H265</tt:Name><tt:UseCount>1</tt:UseCount>
    <tt:Encoding>H265</tt:Encoding>
    <tt:Resolution><tt:Width>640</tt:Width><tt:Height>360</tt:Height></tt:Resolution>
    <tt:Quality>3</tt:Quality>
    <tt:RateControl><tt:FrameRateLimit>15</tt:FrameRateLimit>
     <tt:EncodingInterval>1</tt:EncodingInterval><tt:BitrateLimit>768</tt:BitrateLimit>
    </tt:RateControl>
   </tt:VideoEncoderConfiguration>
  </trt:Profiles>
 </trt:GetProfilesResponse></s:Body>
</s:Envelope>"""


def _device_information_response() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
 <s:Body><tds:GetDeviceInformationResponse>
  <tds:Manufacturer>H-CAM Synthetic</tds:Manufacturer>
  <tds:Model>Phase 2 Simulator</tds:Model>
  <tds:FirmwareVersion>2.0.0-test</tds:FirmwareVersion>
  <tds:SerialNumber>SYNTHETIC-NOT-A-DEVICE</tds:SerialNumber>
  <tds:HardwareId>HCAM-SIM</tds:HardwareId>
 </tds:GetDeviceInformationResponse></s:Body>
</s:Envelope>"""


def _system_date_and_time_response() -> bytes:
    now = datetime.now(UTC)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
 xmlns:tt="http://www.onvif.org/ver10/schema">
 <s:Body><tds:GetSystemDateAndTimeResponse><tds:SystemDateAndTime>
  <tt:UTCDateTime><tt:Time><tt:Hour>{now.hour}</tt:Hour>
   <tt:Minute>{now.minute}</tt:Minute><tt:Second>{now.second}</tt:Second>
  </tt:Time><tt:Date><tt:Year>{now.year}</tt:Year>
   <tt:Month>{now.month}</tt:Month><tt:Day>{now.day}</tt:Day></tt:Date>
  </tt:UTCDateTime>
 </tds:SystemDateAndTime></tds:GetSystemDateAndTimeResponse></s:Body>
</s:Envelope>""".encode("utf-8")


def _services_response(base_url: str, media_url: str | None = None) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:tds="http://www.onvif.org/ver10/device/wsdl"
 xmlns:tt="http://www.onvif.org/ver10/schema">
 <s:Body><tds:GetServicesResponse>
  <tds:Service><tds:Namespace>http://www.onvif.org/ver10/media/wsdl</tds:Namespace>
   <tds:XAddr>{escape(media_url or f'{base_url}/onvif/media_service')}</tds:XAddr>
   <tds:Version><tt:Major>2</tt:Major><tt:Minor>6</tt:Minor></tds:Version>
  </tds:Service>
  <tds:Service><tds:Namespace>http://www.onvif.org/ver20/imaging/wsdl</tds:Namespace>
   <tds:XAddr>{escape(base_url)}/onvif/imaging_service</tds:XAddr>
   <tds:Version><tt:Major>2</tt:Major><tt:Minor>6</tt:Minor></tds:Version>
  </tds:Service>
  <tds:Service><tds:Namespace>http://www.onvif.org/ver10/events/wsdl</tds:Namespace>
   <tds:XAddr>{escape(base_url)}/onvif/events_service</tds:XAddr>
   <tds:Version><tt:Major>2</tt:Major><tt:Minor>6</tt:Minor></tds:Version>
  </tds:Service>
  <tds:Service><tds:Namespace>http://www.onvif.org/ver20/ptz/wsdl</tds:Namespace>
   <tds:XAddr>{escape(base_url)}/onvif/ptz_service</tds:XAddr>
   <tds:Version><tt:Major>2</tt:Major><tt:Minor>6</tt:Minor></tds:Version>
  </tds:Service>
 </tds:GetServicesResponse></s:Body>
</s:Envelope>""".encode("utf-8")


def _imaging_settings_response() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:timg="http://www.onvif.org/ver20/imaging/wsdl"
 xmlns:tt="http://www.onvif.org/ver10/schema">
 <s:Body><timg:GetImagingSettingsResponse><timg:ImagingSettings>
  <tt:Brightness>52</tt:Brightness><tt:ColorSaturation>48</tt:ColorSaturation>
  <tt:Contrast>50</tt:Contrast><tt:Sharpness>44</tt:Sharpness>
  <tt:Exposure><tt:Mode>AUTO</tt:Mode></tt:Exposure>
 </timg:ImagingSettings></timg:GetImagingSettingsResponse></s:Body>
</s:Envelope>"""


def _subscription_response(subscription_url: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:tev="http://www.onvif.org/ver10/events/wsdl"
 xmlns:wsa="http://www.w3.org/2005/08/addressing">
 <s:Body><tev:CreatePullPointSubscriptionResponse>
  <tev:SubscriptionReference><wsa:Address>{escape(subscription_url)}</wsa:Address>
  </tev:SubscriptionReference>
 </tev:CreatePullPointSubscriptionResponse></s:Body>
</s:Envelope>""".encode("utf-8")


def _pull_messages_response() -> bytes:
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:tev="http://www.onvif.org/ver10/events/wsdl"
 xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2"
 xmlns:tt="http://www.onvif.org/ver10/schema">
 <s:Body><tev:PullMessagesResponse><wsnt:NotificationMessage>
  <wsnt:Topic>tns1:RuleEngine/CellMotionDetector/Motion</wsnt:Topic>
  <wsnt:Message><tt:Message UtcTime="{now}" PropertyOperation="Changed">
   <tt:Data><tt:SimpleItem Name="State" Value="true" /></tt:Data>
  </tt:Message></wsnt:Message>
 </wsnt:NotificationMessage></tev:PullMessagesResponse></s:Body>
</s:Envelope>""".encode("utf-8")


def _empty_operation_response(operation: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
 xmlns:tptz="http://www.onvif.org/ver20/ptz/wsdl"
 xmlns:wsnt="http://docs.oasis-open.org/wsn/b-2">
 <s:Body><tptz:{operation}Response /></s:Body>
</s:Envelope>""".encode("utf-8")


def _local_name(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _element_text(root: ElementTree.Element, name: str) -> str | None:
    for element in root.iter():
        if _local_name(element) == name:
            value = (element.text or "").strip()
            return value or None
    return None


def handler_for(
    stream_uri: str,
    *,
    auth_mode: str = "none",
    username: str | None = None,
    password: str | None = None,
    advertised_media_url: str | None = None,
) -> type[BaseHTTPRequestHandler]:
    if auth_mode not in {
        "none",
        "wsse_password_digest",
        "http_digest",
        "wsse_and_http_digest",
    }:
        raise ValueError("unsupported simulator authentication mode")
    if auth_mode != "none" and (not username or not password):
        raise ValueError("authenticated simulator mode requires credentials")
    stream_payload = _stream_uri_response(stream_uri)
    capability_payload = _service_capabilities_response()
    profiles_payload = _profiles_response()
    device_payload = _device_information_response()

    class OnvifSimulatorHandler(BaseHTTPRequestHandler):
        server_version = "HCAM-ONVIF-Simulator/2"
        _realm = "hcam-onvif-synthetic"
        _nonce = "hcam-synthetic-digest-nonce"
        _seen_wsse_tokens: set[str] = set()
        _seen_lock = Lock()
        operation_counts: dict[str, int] = {}

        def _challenge_digest(self) -> None:
            self.send_response(401)
            self.send_header(
                "WWW-Authenticate",
                f'Digest realm="{self._realm}", nonce="{self._nonce}", '
                'algorithm=MD5, qop="auth"',
            )
            self.send_header("Content-Length", "0")
            self.end_headers()

        def _valid_http_digest(self) -> bool:
            authorization = self.headers.get("Authorization", "")
            scheme, separator, parameters = authorization.partition(" ")
            if separator != " " or scheme.lower() != "digest":
                return False
            try:
                values = parse_keqv_list(parse_http_list(parameters))
                if (
                    values.get("username") != username
                    or values.get("realm") != self._realm
                    or values.get("nonce") != self._nonce
                    or values.get("uri") != self.path
                    or values.get("qop") != "auth"
                ):
                    return False
                ha1 = hashlib.md5(  # noqa: S324 - synthetic HTTP Digest fixture
                    f"{username}:{self._realm}:{password}".encode("utf-8"),
                    usedforsecurity=False,
                ).hexdigest()
                ha2 = hashlib.md5(  # noqa: S324 - synthetic HTTP Digest fixture
                    f"POST:{self.path}".encode("ascii"),
                    usedforsecurity=False,
                ).hexdigest()
                expected = hashlib.md5(  # noqa: S324 - synthetic HTTP Digest fixture
                    (
                        f"{ha1}:{self._nonce}:{values['nc']}:"
                        f"{values['cnonce']}:auth:{ha2}"
                    ).encode("ascii"),
                    usedforsecurity=False,
                ).hexdigest()
            except (KeyError, TypeError, ValueError):
                return False
            return hmac.compare_digest(values.get("response", ""), expected)

        def _valid_wsse(self, body: bytes) -> bool:
            try:
                root = ElementTree.fromstring(body)
                supplied_username = _element_text(root, "Username")
                supplied_digest = _element_text(root, "Password")
                nonce_text = _element_text(root, "Nonce")
                created = _element_text(root, "Created")
                if (
                    supplied_username != username
                    or supplied_digest is None
                    or nonce_text is None
                    or created is None
                ):
                    return False
                nonce = base64.b64decode(nonce_text, validate=True)
                timestamp = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if abs((datetime.now(UTC) - timestamp).total_seconds()) > 300:
                    return False
                expected = base64.b64encode(
                    hashlib.sha1(  # noqa: S324 - ONVIF PasswordDigest fixture
                        nonce + created.encode("utf-8") + password.encode("utf-8")
                    ).digest()
                ).decode("ascii")
                replay_key = f"{nonce_text}:{created}"
            except (ElementTree.ParseError, ValueError, TypeError):
                return False
            if not hmac.compare_digest(supplied_digest, expected):
                return False
            with self._seen_lock:
                if replay_key in self._seen_wsse_tokens:
                    return False
                self._seen_wsse_tokens.add(replay_key)
            return True

        def do_POST(self) -> None:  # noqa: N802
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self.send_error(400)
                return
            if content_length < 0 or content_length > 256 * 1024:
                self.send_error(400)
                return
            body = self.rfile.read(content_length) if content_length else b""
            if self.path not in {
                "/onvif/media_service",
                "/onvif/device_service",
                "/onvif/imaging_service",
                "/onvif/events_service",
                "/onvif/ptz_service",
                "/onvif/subscription/hcam",
            }:
                self.send_error(404)
                return
            if content_length < 1:
                self.send_error(400)
                return
            if auth_mode in {"http_digest", "wsse_and_http_digest"}:
                if not self._valid_http_digest():
                    self._challenge_digest()
                    return
            if auth_mode in {"wsse_password_digest", "wsse_and_http_digest"}:
                if not self._valid_wsse(body):
                    self.send_error(401)
                    return
            if b"GetDeviceInformation" in body:
                payload = device_payload
            elif b"GetSystemDateAndTime" in body:
                payload = _system_date_and_time_response()
            elif b"GetServices" in body:
                host = self.headers.get("Host", "127.0.0.1:8081")
                payload = _services_response(
                    f"http://{host}",
                    advertised_media_url,
                )
            elif b"GetStreamUri" in body:
                payload = stream_payload
            elif b"GetServiceCapabilities" in body:
                payload = capability_payload
            elif b"GetProfiles" in body:
                payload = profiles_payload
            elif b"GetImagingSettings" in body:
                payload = _imaging_settings_response()
            elif b"CreatePullPointSubscription" in body:
                host = self.headers.get("Host", "127.0.0.1:8081")
                payload = _subscription_response(
                    f"http://{host}/onvif/subscription/hcam"
                )
            elif b"PullMessages" in body:
                payload = _pull_messages_response()
            elif b"Unsubscribe" in body:
                payload = _empty_operation_response("Unsubscribe")
            elif any(
                operation.encode("ascii") in body
                for operation in (
                    "ContinuousMove",
                    "RelativeMove",
                    "AbsoluteMove",
                    "GotoPreset",
                    "Stop",
                )
            ):
                operation = next(
                    item
                    for item in (
                        "ContinuousMove",
                        "RelativeMove",
                        "AbsoluteMove",
                        "GotoPreset",
                        "Stop",
                    )
                    if item.encode("ascii") in body
                )
                type(self).operation_counts[operation] = (
                    type(self).operation_counts.get(operation, 0) + 1
                )
                payload = _empty_operation_response(operation)
            else:
                self.send_error(400)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/soap+xml; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    return OnvifSimulatorHandler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Controlled H-CAM ONVIF simulator")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument(
        "--stream-uri", default="rtsp://127.0.0.1:8554/synthetic-01"
    )
    parser.add_argument("--allow-non-loopback", action="store_true")
    parser.add_argument(
        "--auth-mode",
        choices=(
            "none",
            "wsse_password_digest",
            "http_digest",
            "wsse_and_http_digest",
        ),
        default="none",
    )
    parser.add_argument("--username")
    parser.add_argument("--password-file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sanitized = sanitize_stream_reference(args.stream_uri)
    if (
        sanitized != args.stream_uri
        or urlsplit(args.stream_uri).scheme not in {"rtsp", "rtsps"}
    ):
        raise SystemExit("--stream-uri must be a credential-free RTSP(S) URI")
    if not 1 <= args.port <= 65535:
        raise SystemExit("--port must be between 1 and 65535")
    if args.bind not in {"127.0.0.1", "::1", "localhost"} and not args.allow_non_loopback:
        raise SystemExit("--allow-non-loopback is required for a non-loopback bind")
    password = None
    if args.auth_mode != "none":
        if not args.username or not args.password_file:
            raise SystemExit("authenticated mode requires --username and --password-file")
        password_path = Path(args.password_file)
        try:
            if not password_path.is_file() or password_path.stat().st_size > 16 * 1024:
                raise OSError
            password = password_path.read_text(encoding="utf-8").rstrip("\r\n")
        except (OSError, UnicodeError) as exc:
            raise SystemExit("--password-file must be a small UTF-8 file") from exc
        if not password or "\n" in password or "\r" in password:
            raise SystemExit("--password-file must contain one non-empty value")
    server = ThreadingHTTPServer(
        (args.bind, args.port),
        handler_for(
            args.stream_uri,
            auth_mode=args.auth_mode,
            username=args.username,
            password=password,
        ),
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
