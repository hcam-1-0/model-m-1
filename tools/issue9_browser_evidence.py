#!/usr/bin/env python3
"""Local-only browser evidence for the generated Sentinel compatibility lab.

The runner intentionally uses neither a provider nor a relay.  It proves the
browser decoder with a generated H.264 fixture, and renders the actual lab
dashboard assets with bounded, display-safe API fixtures at desktop and compact
viewports.  The emitted document is aggregate-only: it contains no media,
locator, token, SDP, camera identifier, or browser command line.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "hcam" / "labs" / "sentinel" / "static"
RESULT_ID = "issue9-browser-result"


class BrowserEvidenceError(RuntimeError):
    """A deterministic browser evidence precondition or assertion failed."""


@dataclass(frozen=True)
class BrowserProbe:
    executable: Path
    family: str


def discover_browser(explicit: str | None = None) -> BrowserProbe:
    candidates: list[tuple[str, str]] = []
    if explicit:
        candidates.append(("explicit", explicit))
    candidates.extend(
        (name, path)
        for name, path in (
            ("chrome", shutil.which("google-chrome")),
            ("chrome", shutil.which("google-chrome-stable")),
            ("chromium", shutil.which("chromium")),
            ("chromium", shutil.which("chromium-browser")),
            ("edge", shutil.which("msedge")),
            ("chrome", r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"),
            ("edge", r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"),
        )
        if path
    )
    for family, candidate in candidates:
        path = Path(candidate)
        if path.is_file():
            return BrowserProbe(path.resolve(), family)
    raise BrowserEvidenceError("browser_not_available")


def discover_ffmpeg(explicit: str | None = None) -> str:
    candidate = explicit or shutil.which("ffmpeg")
    if not candidate:
        raise BrowserEvidenceError("ffmpeg_not_available")
    return candidate


def _fixture_command(ffmpeg: str, output: Path, *, codec: str) -> list[str]:
    encoder = "libx264" if codec == "h264" else "libx265"
    command = [
        ffmpeg,
        "-nostdin",
        "-v",
        "error",
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=320x180:rate=24",
        "-t",
        "3",
        "-an",
        "-c:v",
        encoder,
        "-pix_fmt",
        "yuv420p",
    ]
    if codec == "h264":
        command.extend(("-bf", "0"))
    else:
        command.extend(("-tag:v", "hvc1"))
    command.extend(("-movflags", "+faststart", "-y", str(output)))
    return command


def generate_fixture(ffmpeg: str, root: Path, *, codec: str) -> Path:
    destination = root / f"generated-{codec}.mp4"
    completed = subprocess.run(
        _fixture_command(ffmpeg, destination, codec=codec),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0 or not destination.is_file() or destination.stat().st_size == 0:
        raise BrowserEvidenceError(f"{codec}_fixture_generation_failed")
    return destination


def _video_page(path: str) -> bytes:
    return f"""<!doctype html><meta charset=\"utf-8\"><title>Generated media</title>
<video id=\"preview\" muted autoplay playsinline src=\"/{path}\"></video>
<pre id=\"{RESULT_ID}\">pending</pre>
<script>
const video = document.getElementById('preview');
const result = document.getElementById('{RESULT_ID}');
let first = 0;
setTimeout(() => {{ first = video.currentTime; }}, 700);
setTimeout(() => {{
  result.textContent = JSON.stringify({{
    paused: video.paused, readyState: video.readyState, firstTime: first,
    currentTime: video.currentTime, terminalError: video.error !== null
  }});
}}, 2100);
</script>""".encode("utf-8")


def _dashboard_probe_script() -> bytes:
    return f"""<script>
setTimeout(() => {{
 const root = document.documentElement;
 const status = document.getElementById('inventoryStatus');
 const stale = document.querySelector('.state.stale');
 const disabled = document.querySelector('[data-camera-id]');
 const result = {{
   title: document.getElementById('inventoryTitle')?.textContent || '',
   inventory: status?.textContent || '',
   staleVisible: Boolean(stale),
   previewDisabled: Boolean(disabled?.disabled),
   noHorizontalOverflow: document.body.scrollWidth <= root.clientWidth
 }};
 const node = document.createElement('pre'); node.id = '{RESULT_ID}';
 node.textContent = JSON.stringify(result); document.body.append(node);
}}, 1400);
</script>""".encode("utf-8")


def _safe_camera(*, stale: bool) -> dict[str, object]:
    return {
        "external_camera_id": "generated-display-safe",
        "name": "Generated display-safe camera",
        "location": "Generated zone",
        "lifecycle_state": "stale" if stale else "inactive",
        "observed_health": "unknown",
        "preview_compatible": False,
        "profile_id": "generated-low",
        "media": {"codec": "hevc", "width": 320, "height": 180, "fps": 24},
        "observed_media": {"codec": "hevc", "width": 320, "height": 180},
        "transports": [],
    }


class _EvidenceHandler(SimpleHTTPRequestHandler):
    root: Path
    scenario: str

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _json(self, document: dict[str, object], status: int = 200) -> None:
        payload = json.dumps(document, separators=(",", ":")).encode("ascii")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/media-h264":
            self._send_file(self.root / "generated-h264.mp4", "video/mp4")
            return
        if path == "/media-hevc":
            self._send_file(self.root / "generated-hevc.mp4", "video/mp4")
            return
        if path == "/h264.html":
            self._send_bytes(_video_page("media-h264"), "text/html; charset=utf-8")
            return
        if path == "/hevc.html":
            self._send_bytes(_video_page("media-hevc"), "text/html; charset=utf-8")
            return
        if path == "/":
            page = (STATIC / "dashboard.html").read_bytes().replace(
                b"</body>", _dashboard_probe_script() + b"</body>"
            )
            self._send_bytes(page, "text/html; charset=utf-8")
            return
        if path == "/static/dashboard.js":
            self._send_file(STATIC / "dashboard.js", "text/javascript")
            return
        if path == "/static/dashboard.css":
            self._send_file(STATIC / "dashboard.css", "text/css")
            return
        if path == "/api/status":
            if self.scenario == "malformed":
                self._json({"error": "generated"}, status=503)
                return
            self._json(
                {
                    "classification": "generated-only",
                    "catalog_mode": "generated-fallback",
                    "counts": {"total": 1, "advertised_live": 0},
                    "observed_health_counts": {"online": 0},
                    "runtime_connection_limit": 4 if self.scenario == "capacity" else 0,
                    "source": {"state": "stale" if self.scenario == "stale" else "degraded"},
                    "adapter": {"adapter_id": "generated-adapter"},
                    "media_preparation": {"accelerator": {"h264": {"accelerator": "cpu"}}},
                }
            )
            return
        if path == "/api/cameras":
            self._json({"total": 1, "items": [_safe_camera(stale=self.scenario == "stale")]})
            return
        if path == "/api/events":
            self._json({"total": 0, "items": []})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def _send_file(self, path: Path, media_type: str) -> None:
        self._send_bytes(path.read_bytes(), media_type)

    def _send_bytes(self, payload: bytes, media_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


def _server(root: Path, scenario: str) -> tuple[ThreadingHTTPServer, threading.Thread]:
    handler = type("Issue9EvidenceHandler", (_EvidenceHandler,), {"root": root, "scenario": scenario})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _extract_result(output: str) -> dict[str, Any]:
    matched = re.search(rf'<pre id="{RESULT_ID}">(.*?)</pre>', output, flags=re.DOTALL)
    if not matched:
        raise BrowserEvidenceError("browser_result_missing")
    try:
        document = json.loads(matched.group(1))
    except json.JSONDecodeError as exc:
        raise BrowserEvidenceError("browser_result_invalid") from exc
    if not isinstance(document, dict):
        raise BrowserEvidenceError("browser_result_invalid")
    return document


def _run_browser(browser: BrowserProbe, url: str, *, width: int) -> dict[str, Any]:
    command = [
        str(browser.executable),
        "--headless=new",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--virtual-time-budget=3500",
        f"--window-size={width},800",
        "--dump-dom",
        url,
    ]
    completed = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=45,
    )
    if completed.returncode != 0:
        raise BrowserEvidenceError("browser_execution_failed")
    return _extract_result(completed.stdout)


def run(*, browser_path: str | None, ffmpeg_path: str | None) -> dict[str, object]:
    browser = discover_browser(browser_path)
    ffmpeg = discover_ffmpeg(ffmpeg_path)
    with tempfile.TemporaryDirectory(prefix="hcam-issue9-browser-") as temp:
        root = Path(temp)
        generate_fixture(ffmpeg, root, codec="h264")
        generate_fixture(ffmpeg, root, codec="hevc")
        server, thread = _server(root, "stale")
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            h264 = _run_browser(browser, f"{base}/h264.html", width=1280)
            if (
                h264.get("paused") is not False
                or not isinstance(h264.get("readyState"), int)
                or h264["readyState"] <= 0
                or not isinstance(h264.get("firstTime"), (float, int))
                or not isinstance(h264.get("currentTime"), (float, int))
                or h264["currentTime"] <= h264["firstTime"]
                or h264.get("terminalError") is not False
            ):
                raise BrowserEvidenceError("h264_browser_decode_not_proven")
            desktop = _run_browser(browser, base, width=1280)
            compact = _run_browser(browser, base, width=390)
            if not all(item.get("staleVisible") is True for item in (desktop, compact)):
                raise BrowserEvidenceError("stale_state_not_rendered")
            if not all(item.get("previewDisabled") is True for item in (desktop, compact)):
                raise BrowserEvidenceError("hevc_preview_not_fail_closed")
            if not all(item.get("noHorizontalOverflow") is True for item in (desktop, compact)):
                raise BrowserEvidenceError("dashboard_horizontal_overflow")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    return {
        "schema": "hcam.issue9.browser_evidence.v1",
        "classification": "generated-only",
        "browser_family": browser.family,
        "h264": {"decoded": True, "advancing_current_time": True, "terminal_error": False},
        "hevc": {"preview_compatible": False, "behavior": "fail_closed"},
        "desktop": {"rendered": True, "stale_visible": True, "no_horizontal_overflow": True},
        "compact": {"rendered": True, "stale_visible": True, "no_horizontal_overflow": True},
        "retained_media": False,
        "provider_contacted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local Issue #9 browser media evidence")
    parser.add_argument("--browser")
    parser.add_argument("--ffmpeg")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        evidence = run(browser_path=args.browser, ffmpeg_path=args.ffmpeg)
    except BrowserEvidenceError as exc:
        print(json.dumps({"status": "unsupported", "reason": exc.args[0]}))
        return 2
    encoded = json.dumps(evidence, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="ascii")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
