from __future__ import annotations

from fastapi.testclient import TestClient


def test_request_validation_errors_do_not_echo_rejected_values(
    app,
    editor_headers: dict[str, str],
) -> None:
    headers = {
        **editor_headers,
        "X-HCAM-Reason": "Validate sanitized request errors",
    }
    with TestClient(app) as client:
        response = client.post(
            "/cameras",
            json={
                "camera_id": "invalid id containing secret-must-not-appear",
                "password": "credential-must-not-appear",
            },
            headers=headers,
        )

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"
    assert "secret-must-not-appear" not in response.text
    assert "credential-must-not-appear" not in response.text
    assert all(
        set(item) == {"type", "loc", "msg"}
        for item in response.json()["detail"]
    )
