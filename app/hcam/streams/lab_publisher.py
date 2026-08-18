from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from time import sleep

from hcam.streams.lab import synthetic_stream_id


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="H-CAM synthetic RTSP lab publisher")
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--base-url", default="rtsp://mediamtx:8554/hcam")
    parser.add_argument("--fixture", default="/tmp/hcam-phase2-synthetic.mp4")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--heartbeat-file", type=Path)
    return parser


def _generate_fixture(ffmpeg: str, fixture: Path) -> None:
    completed = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=320x180:rate=10",
            "-t",
            "3",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-tune",
            "zerolatency",
            "-pix_fmt",
            "yuv420p",
            "-g",
            "10",
            "-y",
            str(fixture),
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        raise RuntimeError("could not generate the synthetic H.264 fixture")


def _publisher_command(
    ffmpeg: str,
    fixture: Path,
    destinations: list[str],
) -> list[str]:
    command = [
        ffmpeg,
        "-nostdin",
        "-v",
        "error",
        "-re",
        "-stream_loop",
        "-1",
        "-i",
        str(fixture),
    ]
    for destination in destinations:
        command.extend(
            [
                "-map",
                "0:v:0",
                "-an",
                "-c:v",
                "copy",
                "-f",
                "rtsp",
                "-rtsp_transport",
                "tcp",
                destination,
            ]
        )
    return command


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if os.getenv("HCAM_ALLOW_SYNTHETIC_LAB", "").lower() not in {"1", "true"}:
        print("HCAM_ALLOW_SYNTHETIC_LAB=true is required", file=sys.stderr)
        return 2
    if not 1 <= args.count <= 100:
        print("--count must be between 1 and 100", file=sys.stderr)
        return 2
    fixture = Path(args.fixture)
    _generate_fixture(args.ffmpeg, fixture)
    processes: list[subprocess.Popen[bytes]] = []

    def stop_publishers(_signum=None, _frame=None) -> None:
        for process in processes:
            if process.poll() is None:
                process.terminate()

    signal.signal(signal.SIGTERM, stop_publishers)
    signal.signal(signal.SIGINT, stop_publishers)
    try:
        destinations = [
            f"{args.base_url.rstrip('/')}/{synthetic_stream_id(number)}"
            for number in range(1, args.count + 1)
        ]
        processes.append(
            subprocess.Popen(
                _publisher_command(args.ffmpeg, fixture, destinations),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        )
        while all(process.poll() is None for process in processes):
            if args.heartbeat_file is not None:
                args.heartbeat_file.touch()
            sleep(1)
        return 1
    finally:
        stop_publishers()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        fixture.unlink(missing_ok=True)
        if args.heartbeat_file is not None:
            args.heartbeat_file.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
