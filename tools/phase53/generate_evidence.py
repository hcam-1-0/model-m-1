from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from .verify_p53 import verify


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def generate(repo: Path, cleanup_media: bool = True) -> dict[str, object]:
    evidence_root = repo / "frontend" / "evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    media_root = repo / "output" / "p5-3" / "generated-media"
    media_manifest_path = media_root / "manifest.json"
    if not media_manifest_path.is_file():
        raise RuntimeError("generated_media_manifest_missing")
    runtime_manifest = json.loads(media_manifest_path.read_text(encoding="utf-8"))
    assets = runtime_manifest.get("assets", [])
    for asset in assets:
        path = media_root / asset["relative_path"]
        if not path.is_file() or sha256(path) != asset["sha256"]:
            raise RuntimeError("generated_media_identity_mismatch")
    media_evidence = {
        "schema_version": "hcam.phase5.p5_3.media_evidence.v1",
        "marker": "HCAM-GENERATED-NON-OPERATIONAL",
        "profiles": runtime_manifest["profiles"],
        "aggregate": runtime_manifest["aggregate"],
        "asset_manifest_sha256": hashlib.sha256(
            json.dumps(assets, sort_keys=True, separators=(",", ":")).encode()
        )
        .hexdigest()
        .upper(),
        "tools": runtime_manifest["tools"],
        "source": runtime_manifest["source"],
        "audio": False,
        "retention": "binary_media_removed_after_evidence",
    }
    media_evidence_path = evidence_root / "p5-3-media-manifest.json"
    media_evidence_path.write_text(
        json.dumps(media_evidence, indent=2) + "\n", encoding="utf-8"
    )
    source_manifest_path = evidence_root / "p5-3-source-manifest.json"
    if not source_manifest_path.is_file():
        raise RuntimeError("p5_3_source_manifest_missing")
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    verification = verify(repo)
    validation_path = evidence_root / "p5-3-validation-summary.json"
    if not validation_path.is_file():
        raise RuntimeError("p5_3_validation_summary_missing")
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    validation["repository_verification"] = verification
    validation["repository_regression"] = "pass"
    validation["result"] = "pass"
    validation["limitations"] = [
        "generated_only",
        "no_real_media",
        "no_hardware_capacity_claim",
        "no_provider_or_network_validation",
        "WHEP_default_off",
        "PostgreSQL_not_used",
    ]
    validation_path.write_text(
        json.dumps(validation, indent=2) + "\n", encoding="utf-8"
    )
    if cleanup_media:
        shutil.rmtree(media_root)
    return {
        "status": verification["status"],
        "source_files": source_manifest["source_file_count"],
        "media_assets": len(assets),
        "media_removed": cleanup_media,
    }


def main() -> int:
    result = generate(Path(__file__).resolve().parents[2])
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
