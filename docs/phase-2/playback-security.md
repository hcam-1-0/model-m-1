# Playback Security

The API does not expose an anonymous media URL. An authenticated, department-
authorized viewer requests a playback session with a stated reason. The stream
must be enabled and `healthy` or `degraded`.

The response contains:

- an on-demand fMP4 HLS manifest URL;
- a bearer token;
- an exact expiry timestamp;
- `Cache-Control: no-store` and `Pragma: no-cache`.

## Token Contract

- algorithm: `ES256` with a P-256 private key mounted from a file;
- lifetime: 60 seconds by default, hard-bounded to 10-300 seconds;
- issuer: `hcam-core`;
- audience: `mediamtx`;
- permission: `[{"action":"read","path":"hcam/{stream_id}"}]`;
- unique JTI; only its SHA-256 hash is persisted;
- public key supplied through `/internal/playback-jwks.json`.

MediaMTX checks signature, issuer, audience, expiry, action, and path. A token
for one stream cannot read another. Anonymous HLS is denied. The lab-only
health-worker token is a separate file-mounted credential covering only the
synthetic path pattern; it is not stored in endpoint records.

The HLS service binds to loopback in the lab. TLS termination, production
identity federation, key rotation, browser player integration, and approved
secret-manager wiring are deployment work, not claims made by Phase 2.
