# P3.5 Artifact Research Authorization

Status: `owner_approved_restricted` under `D-P3.5-ARTIFACT-RESEARCH`.

The authorization permits quarantine acquisition of exactly seven artifacts
bound to proposal `P3.5-EXACT-ARTIFACT-REVIEW-PROPOSAL-R0` at SHA-256
`8A027E0C8310C900C7DCA7BDFF0144B9E4E003BCAC1A31853C501226165EAD69`.
The canonical allowlist is
[`p3-5-artifact-research-authorization.json`](../../contracts/phase-3/p3-5-artifact-research-authorization.json).

The approved external slots are three Paddle OCR archives, two Gujarati
Tesseract language-data files, and two Noto variable fonts. The internal
`PLATE-D0` derived artifact remains blocked and is not downloadable.

## Controls

- use only the seven exact credential-free HTTPS URLs;
- disable environment proxies and reject all redirects;
- enforce per-file and 256 MiB cumulative size ceilings;
- store files outside the Git worktree under the configured quarantine root;
- calculate receipts and immutable digests without extracting or executing;
- prohibit runtime loading, dependency changes, inference, training, synthetic
  generation, camera/media access, real/private/Government data, deployment,
  and remote Git operations.

This authority ends at exact artifact research. It does not make the earlier
`D-P3.5-START` statement effective. A completed artifact review packet must be
presented and explicitly accepted before implementation can begin.
