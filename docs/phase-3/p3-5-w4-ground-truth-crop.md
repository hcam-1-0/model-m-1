# P3.5 W4 Ground-Truth Localization And Crop

Status: `validated_complete` under the effective `D-P3.5-START` boundary.

## Scope

`P35-W4_plate_localization_contract_and_generated_ground_truth_crop_path_only`
adds a deterministic, generated-only path from one W3 seed-derived request to:

1. an in-memory `640 x 360` BGR frame;
2. one sealed, normalized ground-truth plate-region contract;
3. a `GT-PLATE-R0` localization result; and
4. one in-memory axis-aligned crop plus a pixel-free crop descriptor.

The input remains the W1/W3 seed-only `DATA-PLATE-GEN-R0` source. The public
generator accepts no file, URL, upload, arbitrary bytes, camera, stream, plate
text, owner, vehicle, watchlist, or Government record.

## Procedural Frame

The stdlib-only generator creates a bounded background and vehicle surface,
then draws the known plate region. Inside that region it draws a
procedural geometry marker, derived ephemerally from the W3 synthetic token.
The marker is not a font, glyph set, script renderer, OCR input adapter, or
claim that a readable registration mark was rendered.

The ephemeral token is used only to make the geometry deterministic. It is not
placed in a contract, snapshot, log, path, URL, identifier, digest commitment,
or persisted evidence field. Frame pixels are held only by the frozen
`GeneratedPlateFrameV1` in-memory object.

## Localization Contract

`PlateLocalizationResultV1` records:

- generated source, generator, frame-generator, and source-frame digests;
- fixed `GT-PLATE-R0` localizer and immutable localizer/runtime versions;
- the `vehicle.registration_plate_region` class;
- normalized bounding box and four-point quadrilateral;
- exact ground-truth confidence and bounded reason/quality codes;
- at most eight hypotheses, with one hypothesis in the W4 fixture; and
- explicit false values for candidate use, model execution, weight loading,
  crop-byte return, image-path return, media-URL return, and plate-text return.

The ground-truth region and split sample are digest-bound. Quadrilaterals must
match their axis-aligned normalized boxes. `PLATE-D0 remains blocked`; W4 does
not create, load, execute, train, or evaluate a localization model.

## Ephemeral Crop

Rectification is a separate deterministic row-slice transform. The crop is
bounded to `512 x 128`, BGR8, and carries an explicit 3x3 source-to-crop
translation matrix. The descriptor records frame, region, crop, generator,
and rectifier lineage.

Pixels remain ephemeral. Only the descriptor may enter canonical evidence;
the in-memory frame and crop dataclasses are rejected by the evidence
serializer. No pixel bytes, plate text, alternatives, file path, media URL, or
token value appears in the tracked W4 fixture.

## Safety And Resources

- execution is default-off and forbidden in production;
- frame maximum is `1280 x 720`;
- plate-region maximum is eight per frame;
- crop maximum is `512 x 128`;
- external input count is zero;
- network, model, artifact, font, and runtime dependency use is zero;
- retention for generated token text and pixels is zero; and
- there is no API, migration, worker, database, outbox, container, or
  deployment change.

## Evidence

The tracked `p3-5-ground-truth-crop-v1.json` fixture contains only the
sanitized localization result and crop descriptor. Focused tests cover exact
20-run replay, both layouts, seed separation, exact source slicing, bounds,
immutability, malformed bytes, lineage and geometry tampering, digest binding,
default-off behavior, and file/network denial.

Final local validation completed with 100 focused P3.5 tests passing, 838 full
repository tests passing, 119 subtests passing, and eight expected
PostgreSQL-only skips. Ruff, analytics/release/P3.5 contract drift checks,
strict P3.5 readiness, source distribution build, and wheel build also pass.
The pre-commit readiness package contains 65 tracked files with zero technical
failures and zero manual gates. Its clean-source digest is regenerated only
after the local commit.

W4 does not authorize W2, W5, OCR, Tesseract, Paddle inference, model or font
loading, cameras, ONVIF, Sentinel media, real/public/private/Government data,
plate-owner correlation, watchlists, operational alerts, remote Git, or
deployment.
