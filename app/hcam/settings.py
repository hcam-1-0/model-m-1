from __future__ import annotations

import ipaddress
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from hcam.streams.network import (
    OnvifEgressRule,
    load_onvif_egress_rules,
    parse_allowed_hosts,
    parse_private_ipv4_networks,
)


_MAX_SECRET_FILE_BYTES = 16 * 1024
_BEARER_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9._~+/=-]{32,256}$")


def _environment_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def _positive_environment_integer(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if parsed < 1:
        raise ValueError(f"{name} must be a positive integer")
    return parsed


def _positive_environment_number(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive number") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be a positive number")
    return parsed


def _read_secret_file(name: str) -> str | None:
    configured_path = os.getenv(name)
    if configured_path is None:
        return None
    if not configured_path.strip():
        raise ValueError(f"{name} must identify a readable secret file")
    path = Path(configured_path).expanduser()
    try:
        if not path.is_file() or path.stat().st_size > _MAX_SECRET_FILE_BYTES:
            raise ValueError(f"{name} must identify a small regular file")
        payload = path.read_bytes()
    except ValueError:
        raise
    except OSError as exc:
        raise ValueError(f"{name} could not be read") from exc
    try:
        value = payload.decode("utf-8").rstrip("\r\n")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{name} must contain UTF-8 text") from exc
    if not value or "\n" in value or "\r" in value or "\x00" in value:
        raise ValueError(f"{name} must contain exactly one non-empty text value")
    return value


def _read_pem_secret_file(name: str) -> str | None:
    configured_path = os.getenv(name)
    if configured_path is None:
        return None
    if not configured_path.strip():
        raise ValueError(f"{name} must identify a readable PEM file")
    path = Path(configured_path).expanduser()
    try:
        if not path.is_file() or path.stat().st_size > 64 * 1024:
            raise ValueError(f"{name} must identify a small regular file")
        value = path.read_text(encoding="ascii")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"{name} could not be read as ASCII PEM") from exc
    if "-----BEGIN" not in value or "PRIVATE KEY-----" not in value:
        raise ValueError(f"{name} must contain a private key PEM")
    return value


def _environment_value_or_file(
    value_name: str,
    file_name: str,
    default: str,
) -> str:
    direct_value = os.getenv(value_name)
    file_value = _read_secret_file(file_name)
    if direct_value is not None and file_value is not None:
        raise ValueError(f"{value_name} and {file_name} are mutually exclusive")
    if file_value is not None:
        return file_value
    if direct_value is not None:
        return direct_value
    return default


def database_url_from_environment(default: str) -> str:
    return _environment_value_or_file(
        "HCAM_DATABASE_URL",
        "HCAM_DATABASE_URL_FILE",
        default,
    )


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = field(default="sqlite:///./var/hcam.db", repr=False)
    create_schema: bool = False
    dev_auth_enabled: bool = False
    service_name: str = "H-CAM Core"
    environment: str = "development"
    max_request_body_bytes: int = 8 * 1024 * 1024
    access_log_enabled: bool = True
    metrics_enabled: bool = False
    metrics_token: str | None = field(default=None, repr=False)
    ffprobe_executable: str = "ffprobe"
    stream_probe_timeout_seconds: float = 8.0
    stream_probe_allowed_hosts: frozenset[str] = frozenset()
    stream_probe_token: str | None = field(default=None, repr=False)
    onvif_egress_rules: tuple[OnvifEgressRule, ...] = ()
    onvif_lab_http_enabled: bool = False
    onvif_ca_bundle: Path | None = None
    onvif_control_enabled: bool = False
    onvif_discovery_enabled: bool = False
    onvif_discovery_interface: str | None = None
    onvif_discovery_allowed_networks: tuple[ipaddress.IPv4Network, ...] = ()
    onvif_discovery_timeout_seconds: float = 2.0
    onvif_discovery_max_results: int = 32
    camera_secret_provider: str = "unconfigured"
    camera_secret_root: Path | None = field(default=None, repr=False)
    playback_signing_key: str | None = field(default=None, repr=False)
    playback_public_base_url: str = "http://127.0.0.1:8888"
    playback_token_ttl_seconds: int = 60
    playback_issuer: str = "hcam-core"
    playback_audience: str = "mediamtx"

    # GIS / PostGIS settings
    postgis_enabled: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: float = 30.0
    db_pool_recycle: int = 1800
    gis_tile_extent: int = 4096
    gis_tile_buffer: int = 256
    gis_max_features_per_tile: int = 10000
    gis_cluster_min_zoom: int = 0
    gis_cluster_max_zoom: int = 20

    def __post_init__(self) -> None:
        environment = self.environment.strip().lower()
        if environment not in {"development", "test", "production"}:
            raise ValueError(
                "HCAM_ENVIRONMENT must be development, test, or production"
            )
        if not self.database_url.strip():
            raise ValueError("HCAM_DATABASE_URL must not be empty")
        if not self.service_name.strip():
            raise ValueError("HCAM_SERVICE_NAME must not be empty")
        if self.max_request_body_bytes < 1:
            raise ValueError("HCAM_MAX_REQUEST_BODY_BYTES must be a positive integer")
        if self.metrics_enabled and self.metrics_token is None:
            raise ValueError(
                "HCAM_METRICS_TOKEN_FILE is required when metrics are enabled"
            )
        if self.metrics_token is not None and _BEARER_TOKEN_PATTERN.fullmatch(
            self.metrics_token
        ) is None:
            raise ValueError(
                "metrics token must be 32 to 256 bearer-safe characters"
            )
        if not self.ffprobe_executable.strip():
            raise ValueError("HCAM_FFPROBE_EXECUTABLE must not be empty")
        if self.stream_probe_timeout_seconds <= 0:
            raise ValueError("HCAM_STREAM_PROBE_TIMEOUT_SECONDS must be positive")
        if self.camera_secret_provider not in {"unconfigured", "file"}:
            raise ValueError(
                "HCAM_CAMERA_SECRET_PROVIDER must be unconfigured or file"
            )
        if self.camera_secret_provider == "file" and self.camera_secret_root is None:
            raise ValueError(
                "HCAM_CAMERA_SECRET_ROOT is required for the file secret provider"
            )
        if self.camera_secret_provider != "file" and self.camera_secret_root is not None:
            raise ValueError(
                "HCAM_CAMERA_SECRET_ROOT requires HCAM_CAMERA_SECRET_PROVIDER=file"
            )
        if environment == "production" and self.camera_secret_provider == "file":
            raise ValueError("the file camera secret provider is forbidden in production")
        if environment == "production" and self.onvif_lab_http_enabled:
            raise ValueError("ONVIF lab HTTP is forbidden in production")
        if environment == "production" and self.onvif_control_enabled:
            raise ValueError("ONVIF control is forbidden in production")
        if environment == "production" and self.onvif_discovery_enabled:
            raise ValueError("ONVIF WS-Discovery is forbidden in production")
        if environment == "production" and any(
            rule.scheme == "http" for rule in self.onvif_egress_rules
        ):
            raise ValueError("production ONVIF egress rules must use HTTPS")
        if self.onvif_ca_bundle is not None:
            ca_bundle = self.onvif_ca_bundle.expanduser().resolve()
            if not ca_bundle.is_file():
                raise ValueError("HCAM_ONVIF_CA_BUNDLE must identify a regular file")
            object.__setattr__(self, "onvif_ca_bundle", ca_bundle)
        if self.onvif_discovery_enabled:
            if self.onvif_discovery_interface is None:
                raise ValueError(
                    "HCAM_ONVIF_DISCOVERY_INTERFACE is required when discovery is enabled"
                )
            if not self.onvif_discovery_allowed_networks:
                raise ValueError(
                    "HCAM_ONVIF_DISCOVERY_ALLOWED_NETWORKS is required when discovery is enabled"
                )
        if self.onvif_discovery_interface is not None:
            try:
                discovery_interface = ipaddress.ip_address(
                    self.onvif_discovery_interface.strip()
                )
            except ValueError as exc:
                raise ValueError(
                    "HCAM_ONVIF_DISCOVERY_INTERFACE must be an IPv4 address"
                ) from exc
            if not isinstance(discovery_interface, ipaddress.IPv4Address):
                raise ValueError(
                    "HCAM_ONVIF_DISCOVERY_INTERFACE must be an IPv4 address"
                )
            if discovery_interface.is_loopback:
                if environment not in {"development", "test"}:
                    raise ValueError("loopback ONVIF discovery is lab-only")
            elif (
                not discovery_interface.is_private
                or discovery_interface.is_link_local
                or discovery_interface.is_multicast
                or discovery_interface.is_unspecified
            ):
                raise ValueError(
                    "HCAM_ONVIF_DISCOVERY_INTERFACE must be a private address"
                )
            if self.onvif_discovery_allowed_networks and not any(
                discovery_interface in network
                for network in self.onvif_discovery_allowed_networks
            ):
                raise ValueError(
                    "ONVIF discovery interface must belong to an approved network"
                )
            object.__setattr__(
                self, "onvif_discovery_interface", str(discovery_interface)
            )
        if not 0.1 <= self.onvif_discovery_timeout_seconds <= 5.0:
            raise ValueError(
                "HCAM_ONVIF_DISCOVERY_TIMEOUT_SECONDS must be between 0.1 and 5"
            )
        if not 1 <= self.onvif_discovery_max_results <= 64:
            raise ValueError(
                "HCAM_ONVIF_DISCOVERY_MAX_RESULTS must be between 1 and 64"
            )
        if self.camera_secret_root is not None:
            secret_root = self.camera_secret_root.expanduser().resolve()
            if not secret_root.is_dir():
                raise ValueError("HCAM_CAMERA_SECRET_ROOT must identify a directory")
            object.__setattr__(self, "camera_secret_root", secret_root)
        playback_url = urlsplit(self.playback_public_base_url)
        if (
            playback_url.scheme not in {"http", "https"}
            or playback_url.hostname is None
            or playback_url.query
            or playback_url.fragment
        ):
            raise ValueError("HCAM_PLAYBACK_PUBLIC_BASE_URL must be an HTTP(S) base URL")
        if not 10 <= self.playback_token_ttl_seconds <= 300:
            raise ValueError("HCAM_PLAYBACK_TOKEN_TTL_SECONDS must be between 10 and 300")
        if not self.playback_issuer.strip() or not self.playback_audience.strip():
            raise ValueError("playback issuer and audience must not be empty")

        # GIS / PostGIS validation
        if self.postgis_enabled and self.database_url.startswith("sqlite"):
            raise ValueError("PostGIS requires PostgreSQL database (not SQLite)")
        if self.db_pool_size < 1:
            raise ValueError("HCAM_DB_POOL_SIZE must be >= 1")
        if self.db_max_overflow < 0:
            raise ValueError("HCAM_DB_MAX_OVERFLOW must be >= 0")
        if self.db_pool_timeout <= 0:
            raise ValueError("HCAM_DB_POOL_TIMEOUT must be positive")
        if self.db_pool_recycle < 0:
            raise ValueError("HCAM_DB_POOL_RECYCLE must be >= 0")
        if self.gis_tile_extent < 256 or self.gis_tile_extent > 8192:
            raise ValueError("HCAM_GIS_TILE_EXTENT must be between 256 and 8192")
        if self.gis_tile_buffer < 0 or self.gis_tile_buffer > 1024:
            raise ValueError("HCAM_GIS_TILE_BUFFER must be between 0 and 1024")
        if self.gis_max_features_per_tile < 100 or self.gis_max_features_per_tile > 50000:
            raise ValueError("HCAM_GIS_MAX_FEATURES_PER_TILE must be between 100 and 50000")
        if not (0 <= self.gis_cluster_min_zoom <= self.gis_cluster_max_zoom <= 22):
            raise ValueError("GIS cluster zoom range must be 0-22 with min <= max")

        object.__setattr__(self, "environment", environment)
        object.__setattr__(self, "database_url", self.database_url.strip())
        object.__setattr__(self, "service_name", self.service_name.strip())
        object.__setattr__(self, "ffprobe_executable", self.ffprobe_executable.strip())
        object.__setattr__(
            self, "playback_public_base_url", self.playback_public_base_url.rstrip("/")
        )
        object.__setattr__(self, "playback_issuer", self.playback_issuer.strip())
        object.__setattr__(self, "playback_audience", self.playback_audience.strip())

    @classmethod
    def from_environment(cls) -> Settings:
        defaults = cls()
        environment = os.getenv("HCAM_ENVIRONMENT", defaults.environment)
        if (
            environment.strip().lower() == "production"
            and os.getenv("HCAM_DATABASE_URL") is None
            and os.getenv("HCAM_DATABASE_URL_FILE") is None
        ):
            raise ValueError(
                "HCAM_DATABASE_URL or HCAM_DATABASE_URL_FILE is required in production"
            )
        return cls(
            database_url=database_url_from_environment(defaults.database_url),
            create_schema=_environment_flag("HCAM_CREATE_SCHEMA"),
            dev_auth_enabled=_environment_flag("HCAM_DEV_AUTH_ENABLED"),
            service_name=os.getenv("HCAM_SERVICE_NAME", defaults.service_name),
            environment=environment,
            max_request_body_bytes=_positive_environment_integer(
                "HCAM_MAX_REQUEST_BODY_BYTES",
                defaults.max_request_body_bytes,
            ),
            access_log_enabled=_environment_flag(
                "HCAM_ACCESS_LOG_ENABLED",
                defaults.access_log_enabled,
            ),
            metrics_enabled=_environment_flag(
                "HCAM_METRICS_ENABLED",
                defaults.metrics_enabled,
            ),
            metrics_token=_read_secret_file("HCAM_METRICS_TOKEN_FILE"),
            ffprobe_executable=os.getenv(
                "HCAM_FFPROBE_EXECUTABLE", defaults.ffprobe_executable
            ),
            stream_probe_timeout_seconds=_positive_environment_number(
                "HCAM_STREAM_PROBE_TIMEOUT_SECONDS",
                defaults.stream_probe_timeout_seconds,
            ),
            stream_probe_allowed_hosts=parse_allowed_hosts(
                os.getenv("HCAM_STREAM_PROBE_ALLOWED_HOSTS")
            ),
            stream_probe_token=_read_secret_file("HCAM_STREAM_PROBE_TOKEN_FILE"),
            onvif_egress_rules=load_onvif_egress_rules(
                os.getenv("HCAM_ONVIF_EGRESS_RULES_FILE")
            ),
            onvif_lab_http_enabled=_environment_flag(
                "HCAM_ONVIF_LAB_HTTP_ENABLED"
            ),
            onvif_ca_bundle=(
                Path(value)
                if (value := os.getenv("HCAM_ONVIF_CA_BUNDLE"))
                else None
            ),
            onvif_control_enabled=_environment_flag(
                "HCAM_ONVIF_CONTROL_ENABLED"
            ),
            onvif_discovery_enabled=_environment_flag(
                "HCAM_ONVIF_DISCOVERY_ENABLED"
            ),
            onvif_discovery_interface=(
                value.strip()
                if (value := os.getenv("HCAM_ONVIF_DISCOVERY_INTERFACE"))
                else None
            ),
            onvif_discovery_allowed_networks=parse_private_ipv4_networks(
                os.getenv("HCAM_ONVIF_DISCOVERY_ALLOWED_NETWORKS")
            ),
            onvif_discovery_timeout_seconds=_positive_environment_number(
                "HCAM_ONVIF_DISCOVERY_TIMEOUT_SECONDS",
                defaults.onvif_discovery_timeout_seconds,
            ),
            onvif_discovery_max_results=_positive_environment_integer(
                "HCAM_ONVIF_DISCOVERY_MAX_RESULTS",
                defaults.onvif_discovery_max_results,
            ),
            camera_secret_provider=os.getenv(
                "HCAM_CAMERA_SECRET_PROVIDER", defaults.camera_secret_provider
            ).strip().lower(),
            camera_secret_root=(
                Path(value)
                if (value := os.getenv("HCAM_CAMERA_SECRET_ROOT"))
                else None
            ),
            playback_signing_key=_read_pem_secret_file(
                "HCAM_PLAYBACK_SIGNING_KEY_FILE"
            ),
            playback_public_base_url=os.getenv(
                "HCAM_PLAYBACK_PUBLIC_BASE_URL", defaults.playback_public_base_url
            ),
            playback_token_ttl_seconds=_positive_environment_integer(
                "HCAM_PLAYBACK_TOKEN_TTL_SECONDS",
                defaults.playback_token_ttl_seconds,
            ),
            playback_issuer=os.getenv(
                "HCAM_PLAYBACK_ISSUER", defaults.playback_issuer
            ),
            playback_audience=os.getenv(
                "HCAM_PLAYBACK_AUDIENCE", defaults.playback_audience
            ),
            postgis_enabled=_environment_flag("HCAM_POSTGIS_ENABLED", defaults.postgis_enabled),
            db_pool_size=_positive_environment_integer(
                "HCAM_DB_POOL_SIZE", defaults.db_pool_size
            ),
            db_max_overflow=_positive_environment_integer(
                "HCAM_DB_MAX_OVERFLOW", defaults.db_max_overflow
            ),
            db_pool_timeout=_positive_environment_number(
                "HCAM_DB_POOL_TIMEOUT", defaults.db_pool_timeout
            ),
            db_pool_recycle=_positive_environment_integer(
                "HCAM_DB_POOL_RECYCLE", defaults.db_pool_recycle
            ),
            gis_tile_extent=_positive_environment_integer(
                "HCAM_GIS_TILE_EXTENT", defaults.gis_tile_extent
            ),
            gis_tile_buffer=_positive_environment_integer(
                "HCAM_GIS_TILE_BUFFER", defaults.gis_tile_buffer
            ),
            gis_max_features_per_tile=_positive_environment_integer(
                "HCAM_GIS_MAX_FEATURES_PER_TILE", defaults.gis_max_features_per_tile
            ),
            gis_cluster_min_zoom=_positive_environment_integer(
                "HCAM_GIS_CLUSTER_MIN_ZOOM", defaults.gis_cluster_min_zoom
            ),
            gis_cluster_max_zoom=_positive_environment_integer(
                "HCAM_GIS_CLUSTER_MAX_ZOOM", defaults.gis_cluster_max_zoom
            ),
        )
