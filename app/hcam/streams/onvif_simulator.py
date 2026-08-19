from __future__ import annotations

import argparse
from collections.abc import Sequence
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
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


def handler_for(stream_uri: str) -> type[BaseHTTPRequestHandler]:
    stream_payload = _stream_uri_response(stream_uri)
    capability_payload = _service_capabilities_response()
    profiles_payload = _profiles_response()

    class OnvifSimulatorHandler(BaseHTTPRequestHandler):
        server_version = "HCAM-ONVIF-Simulator/1"

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
            if self.path != "/onvif/media_service":
                self.send_error(404)
                return
            if content_length < 1:
                self.send_error(400)
                return
            if b"GetStreamUri" in body:
                payload = stream_payload
            elif b"GetServiceCapabilities" in body:
                payload = capability_payload
            elif b"GetProfiles" in body:
                payload = profiles_payload
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
    server = ThreadingHTTPServer((args.bind, args.port), handler_for(args.stream_uri))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
