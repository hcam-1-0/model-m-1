from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx

from .config import AdapterConfig, AdapterConfigurationError, CatalogConfig, StreamConfig


class CatalogLoadError(RuntimeError):
    """A read-only catalog request could not produce approved stream entries."""


@dataclass(frozen=True, slots=True)
class CatalogPreview:
    catalog_host: str
    total_entries: int
    selected_streams: tuple[StreamConfig, ...]


def _catalog_items(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise CatalogLoadError("catalog response must be a JSON object")
    items = payload.get("cameras", payload.get("items"))
    if not isinstance(items, list):
        raise CatalogLoadError("catalog response does not contain a camera list")
    return [item for item in items if isinstance(item, dict)]


def _stream_url_for(item: dict[str, Any], catalog: CatalogConfig) -> str | None:
    if catalog.source_kind == "rtsp":
        value = item.get("rtsp_url")
        return value.strip() if isinstance(value, str) and value.strip() else None

    if catalog.source_kind == "whep":
        value = item.get("webrtc_url")
        return value.strip() if isinstance(value, str) and value.strip() else None

    value = item.get("hls_live_url")
    if not isinstance(value, str) or not value.strip():
        return None
    return urljoin(catalog.url, value.strip())


def load_catalog_preview(config: AdapterConfig) -> CatalogPreview:
    """Fetch only the configured catalog URL and derive bounded, allow-listed streams.

    This intentionally does not crawl paths, discover hosts, follow redirects, or
    contact any camera stream. Stream validation and recording require separate
    explicit admin actions.
    """
    catalog = config.catalog
    if catalog is None:
        raise AdapterConfigurationError("adapter config does not define a catalog")
    if catalog.host not in config.allowed_source_hosts:
        raise AdapterConfigurationError("catalog host is not allow-listed")

    try:
        response = httpx.get(
            catalog.url,
            headers={
                "Accept": "application/json",
                "User-Agent": "H-CAM-Adapter/1.0",
            },
            timeout=catalog.timeout_seconds,
            follow_redirects=False,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise CatalogLoadError("catalog request failed") from exc

    streams: list[StreamConfig] = []
    seen_camera_ids: set[str] = set()
    for item in _catalog_items(payload):
        if item.get("live") is not True:
            continue
        source_id = str(item.get("id", "")).strip()
        if not source_id:
            continue
        stream_url = _stream_url_for(item, catalog)
        if stream_url is None:
            continue
        try:
            source_host = urlsplit(stream_url).hostname
            if source_host is None or source_host.lower().rstrip(".") not in config.allowed_source_hosts:
                continue
            camera_id = f"{catalog.camera_id_prefix}{source_id}"
            if camera_id in seen_camera_ids:
                continue
            streams.append(
                StreamConfig(
                    camera_id=camera_id,
                    rtsp_url=stream_url,
                    location_label=(
                        item.get("location").strip()
                        if isinstance(item.get("location"), str)
                        else None
                    ),
                    department=(
                        item.get("department").strip()
                        if isinstance(item.get("department"), str)
                        else None
                    ),
                )
            )
            seen_camera_ids.add(camera_id)
        except ValueError:
            continue
        if len(streams) >= catalog.max_cameras:
            break

    return CatalogPreview(
        catalog_host=catalog.host,
        total_entries=len(_catalog_items(payload)),
        selected_streams=tuple(streams),
    )
