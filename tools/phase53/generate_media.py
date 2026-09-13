from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

MARKER = "HCAM-GENERATED-NON-OPERATIONAL"
PROFILES = {"C1": 1, "C4": 4, "C10": 10}
RENDITIONS = {
    "low": (640, 360, 10, "500k"),
    "medium": (1280, 720, 20, "1500k"),
    "high": (1920, 1080, 25, "4000k"),
}
MAX_BYTES = 2 * 1024 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def safe_output_root(repo: Path, requested: Path) -> Path:
    expected = (repo / "output" / "p5-3" / "generated-media").resolve()
    actual = requested.resolve()
    if actual != expected:
        raise ValueError("output_root_not_authorized")
    return actual


def tool_record(name: str) -> dict[str, object]:
    location = shutil.which(name)
    if not location:
        raise RuntimeError(f"{name}_not_found")
    path = Path(location).resolve()
    if not path.is_file() or path.stat().st_size > 256 * 1024 * 1024:
        raise RuntimeError(f"{name}_invalid")
    version = subprocess.run(
        [str(path), "-version"], capture_output=True, text=True, timeout=10, check=True
    ).stdout.splitlines()[0][:240]
    return {
        "name": name,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "version": version,
    }


def stream_command(ffmpeg: str, root: Path, stream_number: int) -> list[str]:
    stream_root = root / f"stream-{stream_number:04d}"
    outputs: list[str] = []
    filters: list[str] = []
    split_names = "".join(f"[src_{name}]" for name in RENDITIONS)
    filters.append(f"[0:v]hue=h={stream_number * 23},split=3{split_names}")
    for name, (width, height, fps, bitrate) in RENDITIONS.items():
        rendition_root = stream_root / name
        rendition_root.mkdir(parents=True, exist_ok=True)
        filters.append(
            f"[src_{name}]scale={width}:{height}:flags=fast_bilinear,fps={fps},format=yuv420p[out_{name}]"
        )
        outputs.extend(
            [
                "-map",
                f"[out_{name}]",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-tune",
                "zerolatency",
                "-b:v",
                bitrate,
                "-maxrate",
                bitrate,
                "-bufsize",
                str(int(bitrate[:-1]) * 2) + "k",
                "-g",
                str(fps * 2),
                "-keyint_min",
                str(fps * 2),
                "-sc_threshold",
                "0",
                "-an",
                "-f",
                "hls",
                "-hls_time",
                "2",
                "-hls_list_size",
                "0",
                "-hls_flags",
                "independent_segments",
                "-hls_segment_filename",
                str(rendition_root / "segment-%03d.ts"),
                str(rendition_root / "master.m3u8"),
            ]
        )
    return [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc2=size=1920x1080:rate=25:duration=30",
        "-filter_complex",
        ";".join(filters),
        *outputs,
    ]


def generate_stream(ffmpeg: str, root: Path, stream_number: int) -> dict[str, object]:
    completed = subprocess.run(
        stream_command(ffmpeg, root, stream_number),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=300,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"ffmpeg_failed_stream_{stream_number:04d}")
    return {
        "stream_ref": f"SYN-STREAM-{stream_number:04d}",
        "renditions": list(RENDITIONS),
    }


def generate(profiles: tuple[str, ...], output: Path) -> dict[str, object]:
    repo = Path(__file__).resolve().parents[2]
    root = safe_output_root(repo, output)
    ffmpeg = tool_record("ffmpeg")
    ffprobe = tool_record("ffprobe")
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    stream_count = max(PROFILES[profile] for profile in profiles)
    streams: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=min(4, stream_count)) as executor:
        futures = [
            executor.submit(generate_stream, str(shutil.which("ffmpeg")), root, index)
            for index in range(1, stream_count + 1)
        ]
        for future in as_completed(futures):
            streams.append(future.result())
    assets = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            assets.append(
                {
                    "relative_path": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    total = sum(int(asset["bytes"]) for asset in assets)
    if total > MAX_BYTES:
        shutil.rmtree(root)
        raise RuntimeError("generated_media_size_limit_exceeded")
    manifest = {
        "schema_version": "hcam.phase5.p5_3.generated_media_runtime.v1",
        "marker": MARKER,
        "generated_at": "2026-09-08T09:00:00.000Z",
        "profiles": list(profiles),
        "streams": sorted(streams, key=lambda item: str(item["stream_ref"])),
        "assets": assets,
        "aggregate": {
            "stream_count": stream_count,
            "rendition_count": stream_count * 3,
            "asset_count": len(assets),
            "bytes": total,
        },
        "tools": [ffmpeg, ffprobe],
        "source": "lavfi_testsrc2_only",
        "audio": False,
        "retention": "temporary_untracked_binary_media",
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", default="C1,C4,C10")
    parser.add_argument(
        "--output", type=Path, default=Path("output/p5-3/generated-media")
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profiles = tuple(part.strip() for part in args.profiles.split(",") if part.strip())
    if not profiles or any(profile not in PROFILES for profile in profiles):
        raise SystemExit("invalid_profiles")
    manifest = generate(profiles, args.output)
    print(
        json.dumps(
            {"status": "pass", "aggregate": manifest["aggregate"]}, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
