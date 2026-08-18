from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from fractions import Fraction
from time import perf_counter
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

from hcam.streams.models import StreamEndpoint
from hcam.streams.network import StreamNetworkPolicy, StreamNetworkPolicyError
from hcam.streams.onvif import OnvifResolutionError, OnvifStreamResolver


_MAX_FFPROBE_OUTPUT_BYTES = 1024 * 1024


class ProbeToolError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProbeResult:
    outcome: str
    reason_code: str | None
    latency_ms: float
    media: dict[str, object] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return self.outcome == "success"


def _classify_failure(message: str) -> str:
    normalized = message.lower()
    if any(value in normalized for value in ("401", "403", "unauthorized", "forbidden")):
        return "unauthorized"
    if any(
        value in normalized
        for value in ("protocol not found", "unsupported", "unknown decoder")
    ):
        return "unsupported"
    if any(
        value in normalized
        for value in ("invalid data", "invalid argument", "no such file")
    ):
        return "misconfigured"
    if any(
        value in normalized
        for value in (
            "timed out",
            "connection refused",
            "network is unreachable",
            "host is unreachable",
            "could not resolve",
            "name or service not known",
        )
    ):
        return "unreachable"
    return "probe_failed"


def _frame_rate(value: object) -> float | None:
    if not isinstance(value, str) or value in {"", "0/0"}:
        return None
    try:
        parsed = float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None
    return round(parsed, 3) if parsed >= 0 else None


def _positive_integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _media_summary(payload: dict[str, Any]) -> dict[str, object]:
    streams = payload.get("streams")
    if not isinstance(streams, list):
        streams = []
    video = next(
        (
            item
            for item in streams
            if isinstance(item, dict) and item.get("codec_type") == "video"
        ),
        None,
    )
    if video is None:
        return {}
    format_data = payload.get("format")
    if not isinstance(format_data, dict):
        format_data = {}
    media: dict[str, object] = {}
    for source_key, target_key in (
        ("codec_name", "codec"),
        ("profile", "profile"),
    ):
        value = video.get(source_key)
        if isinstance(value, str) and value:
            media[target_key] = value[:80]
    container = format_data.get("format_name")
    if isinstance(container, str) and container:
        media["container"] = container[:80]
    width = _positive_integer(video.get("width"))
    height = _positive_integer(video.get("height"))
    rate = _frame_rate(video.get("avg_frame_rate") or video.get("r_frame_rate"))
    if width is not None:
        media["width"] = width
    if height is not None:
        media["height"] = height
    if rate is not None:
        media["frame_rate"] = rate
    return media


@dataclass(frozen=True, slots=True)
class FfprobeRunner:
    executable: str = "ffprobe"
    timeout_seconds: float = 8.0

    def probe(
        self,
        locator: str,
        *,
        protocol: str,
        transport: str,
        access_token: str | None = None,
    ) -> ProbeResult:
        timeout_microseconds = str(max(1, int(self.timeout_seconds * 1_000_000)))
        command = [
            self.executable,
            "-v",
            "error",
            "-hide_banner",
            "-rw_timeout",
            timeout_microseconds,
            "-analyzeduration",
            "100000",
            "-probesize",
            "32768",
        ]
        if protocol in {"rtsp", "rtsps"} and transport in {"tcp", "udp"}:
            command.extend(["-rtsp_transport", transport])
        if access_token is not None and protocol not in {"rtsp", "rtsps"}:
            command.extend(["-headers", f"Authorization: Bearer {access_token}\r\n"])
        execution_locator = locator
        if access_token is not None and protocol in {"rtsp", "rtsps"}:
            parsed = urlsplit(locator)
            execution_locator = urlunsplit(
                parsed._replace(query=f"token={quote(access_token, safe='')}")
            )
        command.extend(
            [
                "-show_entries",
                "format=format_name:stream=codec_type,codec_name,profile,width,height,avg_frame_rate,r_frame_rate",
                "-of",
                "json",
                execution_locator,
            ]
        )
        started = perf_counter()
        try:
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
        except FileNotFoundError as exc:
            raise ProbeToolError("ffprobe executable is unavailable") from exc
        except subprocess.TimeoutExpired:
            return ProbeResult(
                outcome="failure",
                reason_code="timeout",
                latency_ms=round((perf_counter() - started) * 1000, 3),
            )
        latency_ms = round((perf_counter() - started) * 1000, 3)
        if (
            len(completed.stdout) > _MAX_FFPROBE_OUTPUT_BYTES
            or len(completed.stderr) > _MAX_FFPROBE_OUTPUT_BYTES
        ):
            raise ProbeToolError("ffprobe output exceeded the safety limit")
        if completed.returncode != 0:
            message = completed.stderr.decode("utf-8", errors="replace")
            return ProbeResult(
                outcome="failure",
                reason_code=_classify_failure(message),
                latency_ms=latency_ms,
            )
        try:
            payload = json.loads(completed.stdout)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProbeToolError("ffprobe returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise ProbeToolError("ffprobe returned an invalid document")
        media = _media_summary(payload)
        if not media:
            return ProbeResult(
                outcome="failure",
                reason_code="unsupported",
                latency_ms=latency_ms,
            )
        return ProbeResult(
            outcome="success",
            reason_code=None,
            latency_ms=latency_ms,
            media=media,
        )


@dataclass(frozen=True, slots=True)
class StreamProbeAdapter:
    runner: FfprobeRunner
    network_policy: StreamNetworkPolicy
    onvif_resolver: OnvifStreamResolver = OnvifStreamResolver()
    access_token: str | None = None

    def probe(self, endpoint: StreamEndpoint) -> ProbeResult:
        if endpoint.secret_ref is not None:
            return ProbeResult("failure", "credentials_unavailable", 0.0)
        try:
            self.network_policy.validate(endpoint.locator)
        except StreamNetworkPolicyError:
            return ProbeResult("failure", "network_policy_denied", 0.0)
        locator = endpoint.locator
        protocol = endpoint.protocol
        if endpoint.adapter_kind == "onvif":
            try:
                locator = self.onvif_resolver.resolve(endpoint.locator)
            except OnvifResolutionError as exc:
                return ProbeResult("failure", exc.reason_code, 0.0)
            try:
                self.network_policy.validate(locator)
            except StreamNetworkPolicyError:
                return ProbeResult("failure", "network_policy_denied", 0.0)
            protocol = "rtsps" if locator.lower().startswith("rtsps://") else "rtsp"
        return self.runner.probe(
            locator,
            protocol=protocol,
            transport=endpoint.transport,
            access_token=self.access_token,
        )
