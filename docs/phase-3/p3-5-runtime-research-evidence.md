# P3.5 Runtime Research Evidence

Evidence ID: `P3.5-RUNTIME-RESEARCH-EVIDENCE-R1`

Decision: `D-P3.5-RUNTIME-RESEARCH`

Status: `complete_pass_owner_accepted_and_start_bound`

This record closes the restricted, non-runtime dependency research authorized
after acceptance of `P3.5-EXACT-ARTIFACT-REVIEW-R1`. It does not authorize
P3.5 implementation, artifact extraction or loading, OCR constructors,
inference, synthetic generation, training, cameras, media, datasets,
Government or private data, deployment, or remote Git operations.

## Exact Environment

- external local quarantine:
  `E:\h-cam-research-cache\phase-3\p3-5-runtime`;
- interpreter: CPython `3.12.13`;
- direct roots: `paddleocr==3.7.0`, `paddlepaddle==3.3.1`,
  `Pillow==12.3.0`, and `regex==2026.7.19`;
- binary wheels: 67 files, 213,980,084 bytes;
- installed distributions: 67;
- native files: 185;
- repository dependency or lockfile changes: none;
- Tesseract runtime: not present and not authorized.

The full wheelhouse and installed environment remain outside Git. Repository
records contain only hashes, normalized inventory, scan evidence, and bounded
metadata.

## Verification Results

| Check | Result |
|---|---|
| Offline installation consistency | `pip check` passed |
| Known-vulnerability audit | 67 dependencies, zero known vulnerabilities |
| Microsoft Defender | Exit 0, no threats found |
| Guarded imports | Exact versions imported successfully |
| Import network guard | One IPv6 socket attempt blocked; zero network access |
| Model, font, media, or traineddata loading | Not performed |
| OCR constructors or inference | Not performed |
| License metadata coverage | 67 of 67 distributions recorded |
| Legal or redistribution approval | Not granted; separate review required |

NetworkX 3.6.1 contains six packaged baseline-test PNG files. Their paths and
containing distribution are inventoried; they were not opened or loaded by the
import check and are not H-CAM datasets or approved runtime inputs.

The blocked IPv6 socket attempt is retained as a security finding. Successful
import proves only that the exact packages can be imported under a denied
network boundary; it is not an OCR, accuracy, compatibility, or deployment
claim.

## Supply-Chain Records

- `p3-5-runtime-research-evidence.json` binds the accepted artifact packet,
  exact environment summary, external evidence hashes, scans, import behavior,
  and remaining blocks.
- `p3-5-runtime-sbom.cdx.json` is a CycloneDX 1.6 inventory containing 67
  package components, 67 wheel components, and 185 native-file components.
  Every component is marked `hcam:runtimeAuthorized=false`.
- `p3-5-runtime-license-review.json` records package license metadata and
  review flags without embedding long raw license bodies. GPL/LGPL/MPL,
  public-domain, and dual-license flags are review prompts, not legal findings.

The SBOM contains 319 components and is byte-identical to the external
quarantine SBOM with SHA-256
`07EE71F79BBD1368F620B7D915E4BF753E23DCC76696862C5E4ADB3CB23ED6DE`.

## Important Limitations

- Tesseract 5 and its native dependency closure remain unresolved, so
  `OCR-G0` and `OCR-G1` execution remain blocked.
- The seven reviewed OCR/font artifacts remain non-runtime quarantine objects;
  they were not extracted or loaded by this research.
- `PLATE-D0` is an internal future artifact and has not been built.
- The dependency audit reports known advisories at the recorded audit time; it
  does not guarantee future absence of vulnerabilities.
- License metadata completeness is not legal, procurement, or redistribution
  approval.
- Network-denied import success does not approve normal runtime networking.
- No accuracy, latency, throughput, hardware compatibility, or conformance
  claim was made.

## Storage Note

`B:` is RaiDrive-backed Google Drive and is prohibited for this work. A partial,
incomplete resolver tree may remain under
`B:\hcam-scan-temp\phase-3\p3-5-runtime`; it is not evidence, is not trusted,
and must not be used. The validated evidence root is the local `E:` path above.

## Gate Resolution

On 2026-08-26, `mayank-admin` supplied final digest-bound `D-P3.5-START` after
review of this evidence. The effective start binds package digest
`915F5E9246A7A656DF528DD54DA6018D7489C6875BF3A77D1A551BAD6EF9AF4D`,
enumerates five loadable artifacts, leaves two Tesseract artifacts blocked, and
permits zero network actions. See
[P3.5 generated-only start authorization](p3-5-start-authorization.md).

This later authorization does not alter the evidence captured here or widen the
research that produced it.
