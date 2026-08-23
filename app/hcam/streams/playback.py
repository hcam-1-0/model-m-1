from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from hcam.audit.repository import AuditRepository
from hcam.camera_registry.models import Camera
from hcam.security.auth import Principal
from hcam.settings import Settings
from hcam.streams.models import PlaybackSession, StreamEndpoint, StreamHealthCurrent
from hcam.streams.schemas import PlaybackSessionResponse


class PlaybackConfigurationError(RuntimeError):
    pass


class PlaybackUnavailableError(RuntimeError):
    pass


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


@dataclass(frozen=True, slots=True)
class PlaybackSigner:
    private_key: ec.EllipticCurvePrivateKey
    key_id: str
    issuer: str
    audience: str
    ttl_seconds: int

    @classmethod
    def from_settings(cls, settings: Settings) -> PlaybackSigner:
        if settings.playback_signing_key is None:
            raise PlaybackConfigurationError("playback signing key is not configured")
        try:
            key = serialization.load_pem_private_key(
                settings.playback_signing_key.encode("ascii"), password=None
            )
        except (ValueError, TypeError, UnicodeError) as exc:
            raise PlaybackConfigurationError("playback signing key is invalid") from exc
        if not isinstance(key, ec.EllipticCurvePrivateKey) or not isinstance(
            key.curve, ec.SECP256R1
        ):
            raise PlaybackConfigurationError("playback signing key must use P-256")
        public_der = key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        key_id = hashlib.sha256(public_der).hexdigest()[:24]
        return cls(
            private_key=key,
            key_id=key_id,
            issuer=settings.playback_issuer,
            audience=settings.playback_audience,
            ttl_seconds=settings.playback_token_ttl_seconds,
        )

    def jwks(self) -> dict[str, object]:
        numbers = self.private_key.public_key().public_numbers()
        return {
            "keys": [
                {
                    "alg": "ES256",
                    "crv": "P-256",
                    "kid": self.key_id,
                    "kty": "EC",
                    "use": "sig",
                    "x": _base64url(numbers.x.to_bytes(32, "big")),
                    "y": _base64url(numbers.y.to_bytes(32, "big")),
                }
            ]
        }

    def issue(
        self,
        *,
        actor_id: str,
        path: str,
        now: datetime,
    ) -> tuple[str, str, datetime]:
        jti = uuid4().hex
        expires_at = now + timedelta(seconds=self.ttl_seconds)
        token = jwt.encode(
            {
                "aud": self.audience,
                "exp": expires_at,
                "iat": now,
                "iss": self.issuer,
                "jti": jti,
                "mediamtx_permissions": [{"action": "read", "path": path}],
                "nbf": now,
                "sub": actor_id,
            },
            self.private_key,
            algorithm="ES256",
            headers={"kid": self.key_id, "typ": "JWT"},
        )
        return token, jti, expires_at


class PlaybackService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.signer = PlaybackSigner.from_settings(settings)

    def create_session(
        self,
        stream_id: str,
        *,
        principal: Principal,
        reason: str,
        request_id: str | None,
        now: datetime | None = None,
    ) -> PlaybackSessionResponse:
        issued_at = now or datetime.now(UTC)
        path = f"hcam/{stream_id}"
        token, jti, expires_at = self.signer.issue(
            actor_id=principal.actor_id,
            path=path,
            now=issued_at,
        )
        session_id = f"pbs_{uuid4().hex}"
        try:
            with self.session.begin():
                endpoint = self.session.get(StreamEndpoint, stream_id)
                health = self.session.get(StreamHealthCurrent, stream_id)
                camera = (
                    self.session.get(Camera, endpoint.camera_id)
                    if endpoint is not None
                    else None
                )
                if (
                    endpoint is None
                    or camera is None
                    or health is None
                    or not principal.can_access_department(camera.department)
                ):
                    raise PlaybackUnavailableError("Stream not found")
                if not endpoint.enabled:
                    raise PlaybackUnavailableError("Stream is disabled")
                if health.state not in {"healthy", "degraded"}:
                    raise PlaybackUnavailableError("Stream is not available for playback")
                self.session.add(
                    PlaybackSession(
                        session_id=session_id,
                        stream_id=stream_id,
                        actor_id=principal.actor_id,
                        path=path,
                        token_jti_hash=hashlib.sha256(jti.encode("ascii")).hexdigest(),
                        created_at=issued_at,
                        expires_at=expires_at,
                    )
                )
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="stream.playback.create",
                    target_type="stream_endpoint",
                    target_id=stream_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="success",
                    context={"camera_id": endpoint.camera_id, "session_id": session_id},
                    request_id=request_id,
                )
        except PlaybackUnavailableError as exc:
            self._record_failure(principal, stream_id, reason, exc, request_id)
            raise
        return PlaybackSessionResponse(
            session_id=session_id,
            stream_id=stream_id,
            playback_url=f"{self.settings.playback_public_base_url}/{path}/index.m3u8",
            access_token=token,
            token_type="Bearer",
            expires_at=expires_at,
        )

    def _record_failure(
        self,
        principal: Principal,
        stream_id: str,
        reason: str,
        error: Exception,
        request_id: str | None,
    ) -> None:
        try:
            with self.session.begin():
                AuditRepository(self.session).record(
                    actor_id=principal.actor_id,
                    action="stream.playback.create",
                    target_type="stream_endpoint",
                    target_id=stream_id,
                    source="hcam.api",
                    reason=reason.strip(),
                    outcome="failure",
                    context={"error_type": type(error).__name__},
                    request_id=request_id,
                )
        except SQLAlchemyError:
            return
