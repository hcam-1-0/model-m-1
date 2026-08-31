from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Header, HTTPException, Query, Response

from hcam.labs.sentinel.fixtures import LabMode, generated_catalog_document


def _document(mode: LabMode, scenario: str) -> tuple[dict[str, object], bytes, str]:
    try:
        document = generated_catalog_document(mode=mode, scenario=scenario)
    except ValueError as exc:
        raise HTTPException(422, "Unsupported generated scenario") from exc
    payload = json.dumps(document, sort_keys=True, separators=(",", ":")).encode(
        "ascii"
    )
    etag = f'"{hashlib.sha256(payload).hexdigest()}"'
    return document, payload, etag


def create_simulator_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        if os.getenv("HCAM_ALLOW_SYNTHETIC_LAB", "").lower() not in {"1", "true"}:
            raise RuntimeError("HCAM_ALLOW_SYNTHETIC_LAB=true is required")
        yield

    app = FastAPI(
        title="H-CAM Phase 2.5 Generated Catalogue",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "classification": "generated-only"}

    @app.get("/api/ingest", response_model=None)
    def ingest(
        response: Response,
        mode: Annotated[LabMode, Query()] = "default",
        scenario: Annotated[str, Query(max_length=32, pattern=r"^[a-z]+$")] = "base",
        if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None,
    ) -> dict[str, object] | Response:
        document, _payload, etag = _document(mode, scenario)
        response.headers["Cache-Control"] = "no-store"
        response.headers["ETag"] = etag
        response.headers["X-HCAM-Data-Classification"] = "generated-only"
        if if_none_match == etag:
            return Response(
                status_code=304, headers={"ETag": etag, "Cache-Control": "no-store"}
            )
        return document

    @app.get("/api/ingest/lab1highadapter", response_model=None)
    def high_adapter(
        response: Response,
        if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None,
    ) -> dict[str, object] | Response:
        document, _payload, etag = _document("default", "base")
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "ETag": etag,
                "X-HCAM-Data-Classification": "generated-only",
                "X-HCAM-Lab-Adapter": "lab1highadapter",
            }
        )
        if if_none_match == etag:
            return Response(
                status_code=304,
                headers={
                    "ETag": etag,
                    "Cache-Control": "no-store",
                    "X-HCAM-Lab-Adapter": "lab1highadapter",
                },
            )
        return document

    @app.get("/api/ingest/lab2lowadapter", response_model=None)
    def low_adapter(
        response: Response,
        if_none_match: Annotated[str | None, Header(alias="If-None-Match")] = None,
    ) -> dict[str, object] | Response:
        document, _payload, etag = _document("low", "base")
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "ETag": etag,
                "X-HCAM-Data-Classification": "generated-only",
                "X-HCAM-Lab-Adapter": "lab2lowadapter",
            }
        )
        if if_none_match == etag:
            return Response(
                status_code=304,
                headers={
                    "ETag": etag,
                    "Cache-Control": "no-store",
                    "X-HCAM-Lab-Adapter": "lab2lowadapter",
                },
            )
        return document

    return app


app = create_simulator_app()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="H-CAM generated Sentinel catalogue simulator"
    )
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    parser.add_argument("--allow-non-loopback", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if (
        args.bind not in {"127.0.0.1", "::1", "localhost"}
        and not args.allow_non_loopback
    ):
        print("non-loopback bind requires --allow-non-loopback")
        return 2
    if not 1 <= args.port <= 65535:
        return 2
    uvicorn.run(app, host=args.bind, port=args.port, access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
