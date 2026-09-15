from __future__ import annotations

from hcam.intelligence.integrations.canonical import digest
from hcam.intelligence.integrations.contracts import ProviderManifestV2


class ManifestError(RuntimeError):
    reason_code = "provider_manifest_invalid"


def manifest_digest(manifest: ProviderManifestV2) -> str:
    return digest(manifest.model_dump(mode="json", exclude={"manifest_digest"}))


class ManifestRegistry:
    def __init__(self) -> None:
        self._items: dict[str, ProviderManifestV2] = {}

    def register(self, manifest: ProviderManifestV2) -> None:
        if manifest.manifest_digest != manifest_digest(manifest):
            raise ManifestError("provider manifest digest does not match")
        if manifest.provider_version_id in self._items:
            raise ManifestError("provider version is already registered")
        self._items[manifest.provider_version_id] = manifest

    def get(self, provider_version_id: str) -> ProviderManifestV2:
        try:
            return self._items[provider_version_id]
        except KeyError as exc:
            raise ManifestError("provider version is not registered") from exc

    def list(self, *, department: str | None = None) -> list[ProviderManifestV2]:
        values = self._items.values()
        if department is not None:
            values = (item for item in values if item.department == department)
        return sorted(values, key=lambda item: (item.provider_key, item.version))
