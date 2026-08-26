# P3.5 Runtime Research Authorization

Status: `owner_approved_restricted`; runtime evidence is pending.

`D-P3.5-RUNTIME-RESEARCH` authorizes an isolated CPython 3.12.13 dependency
review outside the worktree. The direct roots are exactly `paddleocr==3.7.0`,
`paddlepaddle==3.3.1`, `Pillow==12.3.0`, and `regex==2026.7.19`; only their
required binary-wheel transitive closure may be resolved from the official
PyPI hosts.

The external root is
`B:\hcam-scan-temp\phase-3\p3-5-runtime`. The initial new top-level `B:` path
was denied before any package action, so research moved under the existing
empty H-CAM scan directory without changing scope. Repository dependency and
lock files must remain unchanged. The research may produce exact package and
native inventories, license evidence, a CycloneDX SBOM, vulnerability and
Defender results, and import-only proof with socket access denied.

The authorization does not permit source builds, the Tesseract engine, model,
font or traineddata loading, OCR constructors, generation, training, inference,
cameras/media, real/private/Government data, implementation, deployment, or
remote Git actions. Final `D-P3.5-START` remains a separate owner decision.

Canonical record:
[`p3-5-runtime-research-authorization.json`](../../contracts/phase-3/p3-5-runtime-research-authorization.json).
