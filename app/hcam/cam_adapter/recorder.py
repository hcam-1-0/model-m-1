from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Sequence

# ---------------------------------------------------------------------------
# RTSP TCP enforcement — must be set before cv2 import
# ---------------------------------------------------------------------------
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
# Also try to force FFmpeg demuxer to prefer TCP at env level
os.environ["OPENCV_FFMPEG_WRITER_OPTIONS"] = "rtsp_transport;tcp"


def build_ffmpeg_segment_cmd(
    *,
    ffmpeg_bin: str,
    rtsp_url: str,
    output_pattern: str,
    segment_time: int = 300,
    rtsp_transport: str = "tcp",
    extra_input_args: Sequence[str] = (),
    extra_output_args: Sequence[str] = (),
    is_hls: bool | None = None,
) -> list[str]:
    """Build FFmpeg command for zero-re-encode segmented recording.

    - Forces TCP for RTSP via -rtsp_transport tcp
    - Uses -c:v copy -c:a aac (no video re-encode, minimal CPU)
    - Uses -f segment -segment_time N -reset_timestamps 1 -strftime 1
    """
    if is_hls is None:
        is_hls = rtsp_url.lower().endswith(".m3u8") or "m3u8" in rtsp_url.lower()

    cmd: list[str] = [ffmpeg_bin, "-hide_banner", "-loglevel", "warning"]

    # Input side
    if not is_hls and rtsp_transport == "tcp":
        cmd += ["-rtsp_transport", "tcp"]
    # Low-latency / resilience tuning
    cmd += ["-fflags", "+genpts", "-use_wallclock_as_timestamps", "1"]
    cmd += list(extra_input_args)
    cmd += ["-i", rtsp_url]

    # Output side: stream copy + segmentation
    # Use fragmented MP4 (+frag_keyframe+empty_moov) so current segment is playable
    # even if recorder is killed mid-segment; +faststart not needed with frag.
    cmd += [
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "64k",
        "-movflags", "+frag_keyframe+empty_moov+default_base_moof",
        "-f", "segment",
        "-segment_time", str(segment_time),
        "-segment_format", "mp4",
        "-segment_format_options", "movflags=+frag_keyframe+empty_moov+default_base_moof",
        "-reset_timestamps", "1",
        "-strftime", "1",
    ]
    cmd += list(extra_output_args)
    cmd += [output_pattern]
    return cmd


def ensure_camera_dirs(base: Path, camera_id: str) -> tuple[Path, Path, Path]:
    """Create per-camera directory tree. Returns (cam_dir, segments_dir, detections_dir)."""
    cam_dir = base / camera_id
    segments_dir = cam_dir / "segments"
    detections_dir = cam_dir / "detections"
    segments_dir.mkdir(parents=True, exist_ok=True)
    detections_dir.mkdir(parents=True, exist_ok=True)
    return cam_dir, segments_dir, detections_dir


def popen_recorder(cmd: list[str], log_path: Path) -> subprocess.Popen:
    """Launch FFmpeg recorder as subprocess with stderr → log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "ab", buffering=0)
    # Use unbuffered, no shell
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=log_file,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    # Attach log file handle so caller can close it after proc terminates
    proc._log_file = log_file  # type: ignore[attr-defined]
    return proc


def terminate_recorder(proc: subprocess.Popen, timeout: float = 8.0) -> None:
    # Try graceful SIGTERM, then SIGKILL — frag MP4 still playable mid-segment
    try:
        try:
            # Send 'q' via stdin if available (graceful FFmpeg quit) else SIGTERM
            if proc.stdin is not None:
                try:
                    proc.stdin.write(b"q")
                    proc.stdin.flush()
                except Exception:
                    pass
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    finally:
        log_file = getattr(proc, "_log_file", None)
        if log_file is not None:
            try:
                log_file.close()
            except Exception:
                pass


def ffmpeg_cmd_str(cmd: list[str]) -> str:
    return shlex.join(cmd)


def probe_stream_ok(ffprobe_bin: str, rtsp_url: str, timeout: float = 6.0) -> bool:
    """Lightweight ffprobe check — returns True if stream is reachable."""
    cmd = [
        ffprobe_bin, "-v", "error",
        "-rtsp_transport", "tcp",
        "-analyzeduration", "0",
        "-probesize", "512k",
        "-i", rtsp_url,
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
        return result.returncode == 0 and result.stdout.strip() != ""
    except Exception:
        return False
