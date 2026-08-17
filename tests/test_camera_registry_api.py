from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_camera_list_and_detail_return_normalized_records(
    imported_app: FastAPI, viewer_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        list_response = client.get("/cameras", headers=viewer_headers)
        detail_response = client.get(
            "/cameras/synthetic:cctv-001", headers=viewer_headers
        )

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 2
    assert detail_response.status_code == 200
    camera = detail_response.json()
    assert camera["camera_id"] == "synthetic:cctv-001"
    assert camera["version"] == 1
    assert detail_response.headers["etag"] == '"1"'
    assert camera["location"]["latitude"] == 23.0225
    assert camera["state"]["operational"] == "online"
    assert camera["stream"]["reachability"] == "reachable"
    assert camera["stream"]["last_checked_at"].endswith("Z")
    assert camera["stream"]["selected_url"] == "https://camera.example.invalid/streams/1"
    assert "secret" not in detail_response.text
    assert "token" not in detail_response.text


def test_camera_list_supports_model_one_filters(
    imported_app: FastAPI, viewer_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        by_department = client.get(
            "/cameras", params={"department": "traffic"}, headers=viewer_headers
        )
        by_health = client.get(
            "/cameras", params={"health_status": "degraded"}, headers=viewer_headers
        )
        by_status = client.get(
            "/cameras", params={"status": "offline"}, headers=viewer_headers
        )
        by_source = client.get(
            "/cameras",
            params={"source": "synthetic-reference"},
            headers=viewer_headers,
        )

    assert by_department.json()["total"] == 1
    assert by_health.json()["items"][0]["camera_id"] == "synthetic:cctv-002"
    assert by_status.json()["total"] == 1
    assert by_source.json()["total"] == 2


def test_unknown_values_are_explicit_nulls(
    imported_app: FastAPI, viewer_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        response = client.get(
            "/cameras/synthetic:cctv-002", headers=viewer_headers
        )

    camera = response.json()
    assert response.status_code == 200
    assert camera["department"] is None
    assert camera["location"]["latitude"] is None
    assert camera["stream"]["codec"] is None


def test_missing_camera_and_invalid_pagination_are_clear(
    imported_app: FastAPI, viewer_headers: dict[str, str]
) -> None:
    with TestClient(imported_app) as client:
        missing = client.get(
            "/cameras/synthetic:missing", headers=viewer_headers
        )
        invalid_limit = client.get(
            "/cameras", params={"limit": 501}, headers=viewer_headers
        )

    assert missing.status_code == 404
    assert missing.json() == {"detail": "Camera not found"}
    assert invalid_limit.status_code == 422
