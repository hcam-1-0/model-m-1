from __future__ import annotations

import hashlib
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi.testclient import TestClient
from sqlalchemy import select

from hcam.camera_registry.importer import RegistryImporter
from hcam.main import create_app
from hcam.settings import Settings
from hcam.streams.models import PlaybackSession, StreamEndpoint, StreamHealthCurrent
from hcam.streams.playback import PlaybackConfigurationError, PlaybackSigner


def _private_key_pem() -> str:
    key = ec.generate_private_key(ec.SECP256R1())
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("ascii")


def _playback_app(tmp_path: Path, seed_file: Path):
    application = create_app(
        Settings(
            database_url=f"sqlite:///{(tmp_path / 'playback.db').as_posix()}",
            create_schema=True,
            dev_auth_enabled=True,
            environment="test",
            playback_signing_key=_private_key_pem(),
            playback_public_base_url="http://127.0.0.1:8888",
        )
    )
    application.state.database.create_schema()
    RegistryImporter(application.state.database.session_factory).import_file(seed_file)
    with application.state.database.session_factory.begin() as session:
        endpoint = session.scalar(select(StreamEndpoint).where(StreamEndpoint.is_primary))
        assert endpoint is not None
        health = session.get(StreamHealthCurrent, endpoint.stream_id)
        assert health is not None
        health.state = "healthy"
    return application


def test_playback_session_is_short_lived_path_scoped_and_audited(
    tmp_path: Path,
    seed_file: Path,
    viewer_headers: dict[str, str],
) -> None:
    application = _playback_app(tmp_path, seed_file)
    headers = {**viewer_headers, "X-HCAM-Reason": "Authorized live stream review"}
    try:
        with application.state.database.session_factory() as session:
            stream_id = session.scalar(
                select(StreamEndpoint.stream_id).where(StreamEndpoint.is_primary)
            )
        assert stream_id is not None
        with TestClient(application) as client:
            response = client.post(
                f"/streams/{stream_id}/playback-sessions", headers=headers
            )
            jwks_response = client.get("/internal/playback-jwks.json")

        assert response.status_code == 201
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["Pragma"] == "no-cache"
        payload = response.json()
        assert payload["playback_url"] == (
            f"http://127.0.0.1:8888/hcam/{stream_id}/index.m3u8"
        )
        assert payload["token_type"] == "Bearer"
        assert jwks_response.status_code == 200
        assert jwks_response.headers["Cache-Control"] == "no-store"
        jwk = jwt.PyJWK.from_dict(jwks_response.json()["keys"][0])
        claims = jwt.decode(
            payload["access_token"],
            jwk.key,
            algorithms=["ES256"],
            audience="mediamtx",
            issuer="hcam-core",
        )
        assert claims["sub"] == viewer_headers["X-HCAM-Actor"]
        assert claims["exp"] - claims["iat"] == 60
        assert claims["mediamtx_permissions"] == [
            {"action": "read", "path": f"hcam/{stream_id}"}
        ]
        with application.state.database.session_factory() as session:
            record = session.scalar(select(PlaybackSession))
            assert record is not None
            assert record.stream_id == stream_id
            assert record.token_jti_hash == hashlib.sha256(
                claims["jti"].encode("ascii")
            ).hexdigest()
            assert payload["access_token"] not in repr(record.__dict__)
    finally:
        application.state.database.dispose()


def test_playback_rejects_unhealthy_stream_without_issuing_token(
    tmp_path: Path,
    seed_file: Path,
    viewer_headers: dict[str, str],
) -> None:
    application = _playback_app(tmp_path, seed_file)
    headers = {**viewer_headers, "X-HCAM-Reason": "Authorized live stream review"}
    try:
        with application.state.database.session_factory.begin() as session:
            health = session.scalar(select(StreamHealthCurrent))
            assert health is not None
            health.state = "offline"
            stream_id = health.stream_id
        with TestClient(application) as client:
            response = client.post(
                f"/streams/{stream_id}/playback-sessions", headers=headers
            )
        assert response.status_code == 409
        assert "access_token" not in response.text
        with application.state.database.session_factory() as session:
            assert session.scalar(select(PlaybackSession)) is None
    finally:
        application.state.database.dispose()


def test_playback_is_unavailable_without_signing_key(
    imported_app,
    viewer_headers: dict[str, str],
) -> None:
    headers = {**viewer_headers, "X-HCAM-Reason": "Authorized live stream review"}
    stream_id = _stream_id(imported_app)
    with TestClient(imported_app) as client:
        response = client.post(
            f"/streams/{stream_id}/playback-sessions", headers=headers
        )
        jwks = client.get("/internal/playback-jwks.json")
    assert response.status_code == 503
    assert jwks.status_code == 503


def _stream_id(application) -> str:
    with application.state.database.session_factory() as session:
        stream_id = session.scalar(select(StreamEndpoint.stream_id))
    assert stream_id is not None
    return stream_id


@pytest.mark.parametrize("key_kind", ["invalid", "rsa", "p384"])
def test_playback_signer_rejects_invalid_or_non_p256_keys(key_kind: str) -> None:
    if key_kind == "invalid":
        pem = "not-a-private-key"
    elif key_kind == "rsa":
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("ascii")
    else:
        key = ec.generate_private_key(ec.SECP384R1())
        pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("ascii")

    with pytest.raises(PlaybackConfigurationError):
        PlaybackSigner.from_settings(Settings(playback_signing_key=pem))


def test_playback_hides_missing_or_out_of_scope_stream(
    tmp_path: Path,
    seed_file: Path,
    viewer_headers: dict[str, str],
) -> None:
    application = _playback_app(tmp_path, seed_file)
    scoped = {
        **viewer_headers,
        "X-HCAM-Departments": "not-the-camera-department",
        "X-HCAM-Reason": "Authorized scoped playback review",
    }
    try:
        stream_id = _stream_id(application)
        with TestClient(application) as client:
            hidden = client.post(
                f"/streams/{stream_id}/playback-sessions", headers=scoped
            )
            missing = client.post(
                f"/streams/str_{'f' * 32}/playback-sessions", headers=scoped
            )
        assert hidden.status_code == 404
        assert missing.status_code == 404
    finally:
        application.state.database.dispose()


def test_playback_rejects_disabled_stream(
    tmp_path: Path,
    seed_file: Path,
    viewer_headers: dict[str, str],
) -> None:
    application = _playback_app(tmp_path, seed_file)
    headers = {**viewer_headers, "X-HCAM-Reason": "Authorized live stream review"}
    try:
        with application.state.database.session_factory.begin() as session:
            endpoint = session.scalar(select(StreamEndpoint))
            assert endpoint is not None
            endpoint.enabled = False
            stream_id = endpoint.stream_id
        with TestClient(application) as client:
            response = client.post(
                f"/streams/{stream_id}/playback-sessions", headers=headers
            )
        assert response.status_code == 409
        assert response.json()["detail"] == "Stream is disabled"
    finally:
        application.state.database.dispose()
