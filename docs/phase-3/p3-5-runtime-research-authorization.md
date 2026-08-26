# P3.5 Runtime Research Authorization

Status: `owner_approved_restricted`; runtime evidence is pending.

`D-P3.5-RUNTIME-RESEARCH` authorizes an isolated CPython 3.12.13 dependency
review outside the worktree. The direct roots are exactly `paddleocr==3.7.0`,
`paddlepaddle==3.3.1`, `Pillow==12.3.0`, and `regex==2026.7.19`; only their
required binary-wheel transitive closure may be resolved from the official
PyPI hosts.

The external root is
`E:\h-cam-research-cache\phase-3\p3-5-runtime`. The initial `B:` path was
denied before package action. A second `B:` attempt began dependency resolution
but was stopped before any complete wheelhouse or installation when the owner
identified `B:` as RaiDrive Google Drive and prohibited further use. Local
space was then made available on `E:` without changing scope. Repository dependency and
lock files must remain unchanged. The research may produce exact package and
native inventories, license evidence, a CycloneDX SBOM, vulnerability and
Defender results, and import-only proof with socket access denied.

The authorization does not permit source builds, the Tesseract engine, model,
font or traineddata loading, OCR constructors, generation, training, inference,
cameras/media, real/private/Government data, implementation, deployment, or
remote Git actions. At this research-authorization checkpoint, final
`D-P3.5-START` remained a separate owner decision; its later restricted scope
is recorded in
[P3.5 generated-only start authorization](p3-5-start-authorization.md).

Canonical record:
[`p3-5-runtime-research-authorization.json`](../../contracts/phase-3/p3-5-runtime-research-authorization.json).
