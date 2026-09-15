# P5.7 Limitations

- All product, browser, workload, and evidence inputs are generated-only; no Government, police, private, identity, biometric, vehicle, watchlist, case, investigation, or real evidence data was used.
- Validation used local loopback static bundles and installed Microsoft Edge only; it is not physical-device, assistive-technology, multi-monitor, server, cluster, hardware-capacity, or production evidence.
- Playwright Chromium revision 1243, Firefox, and WebKit were unavailable. An incompatible cached Chromium revision 1223 was not executed, and no browser was downloaded.
- Manual WCAG protocols and independent WCAG-EM-style evaluation remain required; automated accessibility checks are not a conformance claim.
- Sixteen PostgreSQL integration tests were skipped because HCAM_POSTGRES_TEST_URL was not configured; no database, RLS, backup, restore, or recovery execution is claimed.
- The dependency lockfile, SBOM, and prior vulnerability evidence were preserved without refresh; no scanner, install, update, download, SLSA, or independent reproducibility claim is made.
- Two broad non-evidentiary Playwright invocations selected unrelated legacy specs and exceeded outer shell bounds; they were discarded and replaced by explicit P5.7 per-spec runs with 392 of 392 checks passing.
- No provider, Sentinel, camera, tile, media, model, inference, telemetry backend, operational action, container, Kubernetes, deployment, release, or remote Git action was authorized or executed.
