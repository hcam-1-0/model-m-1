# Issue #9 cross-platform compatibility and browser-media matrix

This is the deterministic CI contract for the generated-only Sentinel
Compatibility Lab. It does not authorize a public Sentinel provider, real
camera media, or persistent media capture.

## Required offline checks

| OS | Python | Runtime | Browser/codec | Accelerator | State | Evidence source | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Linux | 3.12, `uv sync --locked` | Host-native generated fixture | Chromium H.264 | CPU | SUPPORTED | `tools/issue9_browser_evidence.py` | Platform engineering |
| Linux | 3.12, `uv sync --locked` | Docker Compose generated lab | N/A | CPU | SUPPORTED | `tools/phase2_publication_evidence.py compose` | Platform engineering |
| Windows | 3.12, `uv sync --locked` | Host-native generated fixture | Browser preparation and asset checks | CPU | SUPPORTED | Issue #9 Windows workflow job | Platform engineering |
| Linux | 3.12 | Docker Compose generated lab | N/A | NVIDIA | OPTIONAL | Compose NVIDIA configuration validation | Media platform |
| Linux | 3.12 | Docker Compose generated lab | N/A | Intel/VAAPI | OPTIONAL | Compose VAAPI configuration validation | Media platform |
| Linux | 3.12 | Docker Compose generated lab | N/A | AMD/VAAPI | OPTIONAL | Compose VAAPI configuration validation | Media platform |
| Any unsupported runner | 3.12 | Any | Any | unavailable hardware | UNSUPPORTED | capability detector reports not-present | Media platform |

`OPTIONAL` means configuration is validated without asserting hardware execution.
There is no GPU green result unless the capability detector identifies the
hardware and the explicit hardware workflow is run.

The local browser runner renders the actual Sentinel dashboard files at desktop
(1280px) and compact (390px) widths with a bounded stale display-safe catalogue.
It separately generates H.264 and HEVC fixtures. H.264 success requires a real
HTML video element that is not paused, has positive `readyState`, advances
`currentTime`, and has no terminal error. HEVC is represented by a display-safe
camera with `preview_compatible: false`; it is not counted as browser preview.

## Fault and lifecycle evidence

The existing generated-lab test suites exercise disconnect, stale, malformed,
and capacity fault requests plus bounded recovery. The browser runner proves the
stale presentation and HEVC fail-closed control at both viewport sizes. A media
API response, WHEP answer, or peer connection alone is never reported as decoded
browser media evidence.

Every supported execution clears generated fixtures with
`remove_media_fixtures`, stops Compose with `down --volumes --remove-orphans`,
and emits only aggregate evidence. Evidence manifests must not contain provider
locators, stream URLs, credentials, bearer tokens, SDP, camera identifiers,
media files, or frame captures.
`tools/issue9_evidence_safety.py` validates that contract immediately before the
browser evidence artifact is uploaded.

## Required-check and branch-protection inventory

Repository administrators should require the Issue #9 **Offline compatibility
matrix** workflow and existing Python CI checks for pull requests to `main`.
Require one approving review, dismiss stale approvals, require branch-up-to-date,
and prohibit force pushes/deletions. The **Sentinel external provider (opt-in)**
workflow is informational: it is dispatched manually or scheduled, receives no
provider URL by default, and is not a merge requirement. GPU preparation is
required configuration validation; hardware evidence remains informational and
capability-detected.
