from __future__ import annotations

import argparse
import os
import signal
from collections.abc import Sequence
from pathlib import Path
from threading import Event


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="No-media standby for the online Sentinel compatibility lab"
    )
    parser.add_argument("--heartbeat-file", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if os.getenv("HCAM_ALLOW_SENTINEL_SANDBOX", "").lower() not in {"1", "true"}:
        return 2
    stopping = Event()

    def stop(_signum: int, _frame: object) -> None:
        stopping.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopping.wait(1):
        args.heartbeat_file.touch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
