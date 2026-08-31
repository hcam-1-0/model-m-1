from __future__ import annotations

import argparse
import asyncio
import os
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path

from hcam.labs.sentinel.faults import (
    FaultRequestError,
    atomic_write_json,
    read_fault_request,
)


async def _copy(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while data := await reader.read(64 * 1024):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.CancelledError):
        pass
    finally:
        writer.close()
        with suppress(ConnectionError):
            await writer.wait_closed()


def fault_is_active(request_path: Path) -> tuple[bool, str | None]:
    try:
        request = read_fault_request(request_path)
    except FaultRequestError:
        return False, "invalid_request"
    if request is None or request.scenario != "F6" or request.camera_id != "C04":
        return False, None
    return request.active(), request.request_id


async def run_proxy(
    *,
    bind: str,
    port: int,
    upstream_host: str,
    upstream_port: int,
    request_path: Path,
    status_path: Path,
) -> None:
    if os.getenv("HCAM_ALLOW_SYNTHETIC_LAB", "").lower() not in {"1", "true"}:
        raise RuntimeError("HCAM_ALLOW_SYNTHETIC_LAB=true is required")
    if upstream_host != "mediamtx" or upstream_port != 8554:
        raise RuntimeError("exact generated-lab upstream is required")

    async def handle(
        client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter
    ) -> None:
        blocked, request_id = fault_is_active(request_path)
        atomic_write_json(
            status_path,
            {
                "classification": "generated-only",
                "component": "rtsp-fault-proxy",
                "request_id": request_id,
                "inference_blocked": blocked,
                "preview_path_affected": False,
            },
        )
        if blocked:
            client_writer.close()
            await client_writer.wait_closed()
            return
        try:
            upstream_reader, upstream_writer = await asyncio.wait_for(
                asyncio.open_connection(upstream_host, upstream_port), timeout=5
            )
        except (OSError, TimeoutError):
            client_writer.close()
            await client_writer.wait_closed()
            return
        await asyncio.gather(
            _copy(client_reader, upstream_writer),
            _copy(upstream_reader, client_writer),
        )

    server = await asyncio.start_server(handle, bind, port)
    atomic_write_json(
        status_path,
        {
            "classification": "generated-only",
            "component": "rtsp-fault-proxy",
            "ready": True,
            "inference_blocked": False,
            "preview_path_affected": False,
        },
    )
    async with server:
        await server.serve_forever()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Private Phase 2.5 RTSP fault proxy")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8555)
    parser.add_argument("--upstream-host", default="mediamtx")
    parser.add_argument("--upstream-port", type=int, default=8554)
    parser.add_argument("--request-path", type=Path, required=True)
    parser.add_argument("--status-path", type=Path, required=True)
    parser.add_argument("--allow-non-loopback", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if (
        args.bind not in {"127.0.0.1", "::1", "localhost"}
        and not args.allow_non_loopback
    ):
        return 2
    if not 1 <= args.port <= 65535:
        return 2
    try:
        asyncio.run(
            run_proxy(
                bind=args.bind,
                port=args.port,
                upstream_host=args.upstream_host,
                upstream_port=args.upstream_port,
                request_path=args.request_path,
                status_path=args.status_path,
            )
        )
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
