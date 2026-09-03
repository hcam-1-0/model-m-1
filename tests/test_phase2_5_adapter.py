from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from hcam.labs.sentinel.adapter import CatalogAdapterError, SentinelCatalogAdapter
from hcam.labs.sentinel.fixtures import generated_catalog_document
from hcam.labs.sentinel.models import ExactNetworkPolicy, NetworkRule
from hcam.labs.sentinel.secrets import FileSecretProvider, SecretResolutionError
from hcam.labs.sentinel.store import CatalogStore


def policy() -> ExactNetworkPolicy:
    return ExactNetworkPolicy(
        (
            NetworkRule("http", "catalog-simulator", 8090, "/api/ingest"),
            NetworkRule("rtsp", "mediamtx", 8554, "/hcam/"),
            NetworkRule("rtsp", "rtsp-fault-proxy", 8555, "/hcam/"),
            NetworkRule("http", "mediamtx", 8889, "/hcam/"),
            NetworkRule("http", "mediamtx", 8888, "/hcam/"),
        )
    )


def make_store(tmp_path, *, auth_mode: str = "none", secret_ref: str | None = None) -> CatalogStore:
    store = CatalogStore(tmp_path / "phase2-5.db")
    store.initialize()
    store.upsert_source(
        source_id="generated-sentinel",
        catalog_locator="http://catalog-simulator:8090/api/ingest",
        auth_mode=auth_mode,
        secret_ref=secret_ref,
    )
    return store


def test_adapter_refreshes_then_reuses_etag(tmp_path) -> None:
    payload = json.dumps(generated_catalog_document()).encode("utf-8")
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        assert request.url.host == "catalog-simulator"
        if request.headers.get("if-none-match") == '"generated-v1"':
            return httpx.Response(304, headers={"ETag": '"generated-v1"'})
        return httpx.Response(200, content=payload, headers={"ETag": '"generated-v1"'})

    store = make_store(tmp_path)
    adapter = SentinelCatalogAdapter(store, policy(), transport=httpx.MockTransport(handler))
    first = asyncio.run(
        adapter.refresh(
            "generated-sentinel", requester="pytest", reason="generated catalogue baseline"
        )
    )
    second = asyncio.run(
        adapter.refresh(
            "generated-sentinel", requester="pytest", reason="generated catalogue unchanged"
        )
    )

    assert first.record_count == 50
    assert not first.unchanged
    assert second.unchanged
    assert first.snapshot_id == second.snapshot_id
    assert requests == 2
    assert store.summary("generated-sentinel")["counts"]["advertised_live"] == 30


def test_adapter_stops_reading_oversized_response(tmp_path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"{" + b"x" * 4096)

    adapter = SentinelCatalogAdapter(
        make_store(tmp_path),
        policy(),
        max_response_bytes=1024,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(CatalogAdapterError, match="catalog_response_too_large"):
        asyncio.run(
            adapter.refresh(
                "generated-sentinel", requester="pytest", reason="oversized generated response"
            )
        )


@pytest.mark.parametrize("status", (301, 401, 403, 404))
def test_adapter_rejects_redirect_auth_and_unexpected_status(tmp_path, status: int) -> None:
    adapter = SentinelCatalogAdapter(
        make_store(tmp_path),
        policy(),
        transport=httpx.MockTransport(lambda _request: httpx.Response(status)),
    )

    with pytest.raises(CatalogAdapterError):
        asyncio.run(
            adapter.refresh(
                "generated-sentinel", requester="pytest", reason="safe status handling"
            )
        )


def test_file_secret_provider_supports_rotation_and_denies_traversal(tmp_path) -> None:
    root = tmp_path / "secrets"
    root.mkdir()
    secret = root / "catalog.json"
    secret.write_text('{"bearer_token":"first"}', encoding="utf-8")
    provider = FileSecretProvider(root)

    assert provider.resolve("catalog.json", "bearer").bearer_token == "first"
    secret.write_text('{"bearer_token":"second"}', encoding="utf-8")
    assert provider.resolve("catalog.json", "bearer").bearer_token == "second"
    with pytest.raises(SecretResolutionError, match="secret_ref_invalid"):
        provider.resolve("../catalog.json", "bearer")


def test_adapter_resolves_bearer_secret_for_each_attempt(tmp_path) -> None:
    root = tmp_path / "secrets"
    root.mkdir()
    (root / "catalog.json").write_text('{"bearer_token":"rotated-token"}', encoding="utf-8")
    seen_header = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_header
        seen_header = request.headers.get("authorization", "")
        return httpx.Response(200, json=generated_catalog_document())

    store = make_store(tmp_path, auth_mode="bearer", secret_ref="catalog.json")
    adapter = SentinelCatalogAdapter(
        store,
        policy(),
        secret_provider=FileSecretProvider(root),
        transport=httpx.MockTransport(handler),
    )
    asyncio.run(
        adapter.refresh(
            "generated-sentinel", requester="pytest", reason="typed secret provider validation"
        )
    )

    assert seen_header == "Bearer rotated-token"
    assert "rotated-token" not in str(store.list_events("generated-sentinel"))
