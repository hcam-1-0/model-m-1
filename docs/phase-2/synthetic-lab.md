# Synthetic 50-Stream Lab

The lab is disposable and contains no Government data or real-person footage.
One generated 320x180 H.264 test pattern is looped and remuxed to 50 independent
RTSP paths. Remuxing avoids 50 simultaneous encoders while preserving 50 media
sessions, health records, leases, and HLS paths.

Components:

- PostgreSQL 18 and one-shot Alembic migration;
- H-CAM API with local test identity headers;
- MediaMTX `1.19.3-ffmpeg` pinned by digest;
- one controlled ONVIF SOAP simulator;
- one 50-output synthetic publisher;
- two PostgreSQL-safe health-worker replicas;
- one transactional outbox dispatcher with a metadata-only validation sink;
- 50 deterministic cameras and stream endpoints.

Only `127.0.0.1:8000` (API) and `127.0.0.1:8888` (HLS) are published. RTSP,
MediaMTX API, MediaMTX metrics, PostgreSQL, and ONVIF remain on the private
Compose network. Recording is disabled globally and per path.

## Commands

```powershell
python tools/phase2_lab.py prepare
python tools/phase2_lab.py doctor
python tools/phase2_lab.py config
python tools/phase2_lab.py start
python tools/phase2_lab.py verify --timeout 360
python tools/phase2_lab.py stop
```

`verify` requires all 50 streams to reach `healthy`, obtains a path-scoped
playback session, reads only a bounded HLS manifest, proves anonymous access is
denied, and proves the token cannot read a second stream. It never downloads
segments or stores video.

The failure drill stops the controlled ONVIF simulator, forces three failed
probes on its synthetic stream, verifies `offline`, restarts the simulator, and
restores that stream with two successes. The isolated adapter outage leaves the
media relay and the other 49 streams running. The drill then requires two fresh
successful probe rounds across the complete 50-stream fleet and fails unless
every stream returns `healthy`.

Secrets are generated under ignored `var/phase2-lab-secrets/`. They are local
test credentials, not production credentials. On POSIX hosts the directory is
mode `0700`; its files are mode `0644` because Linux Compose preserves host
ownership for file-backed secrets and the fixed non-root application UID must
read the service-specific mounts. Other host users cannot traverse the private
directory, and each container receives only the secrets declared for that
service. `stop` removes the disposable database volume.
