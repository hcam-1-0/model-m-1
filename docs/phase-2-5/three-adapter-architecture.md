# H-CAM Three-Adapter Architecture

Status: two online Sentinel lab profiles and their generated fallback are
implemented; the future main adapter remains independent and unmodified.

## Adapter Boundaries

H-CAM now distinguishes three architectural adapter roles:

| Adapter | Scope | Current online records | Connection / preview ceiling | Quality policy |
| --- | --- | ---: | ---: | --- |
| Future main adapter | Product and deployment architecture | Dynamic | Dynamic | Product decisions and gates; no lab dependency |
| `lab1highadapter` | High-resource Sentinel sandbox lab | 30 in a 50-slot holder | 30 connections / 4 previews | Native catalogue media; no downgrade |
| `lab2lowadapter` | Lower-resource Sentinel sandbox lab | Same 30 in a 50-slot holder | 4 connections / 1 preview | Same native catalogue media; no downgrade |

The future main adapter is not a hidden alias of either lab adapter. Product
code does not import `hcam.labs.sentinel`, and neither lab adapter is a runtime
dependency of the main platform.

## Shared Core, Separate Profiles

The two lab adapters share the bounded, read-only catalogue transport,
normalization, exact network policy, credential boundary, durable catalogue
store, live source inventory, dashboard, and WHEP relay. Both use the same
public `/api/ingest` endpoint. They differ only in an explicit immutable local
resource profile:

- maximum managed stream connections;
- maximum concurrent browser preview sessions; and
- resource classification exposed by the lab status API.

Switching profiles does not change camera IDs, advertised quality, codec,
resolution, FPS, bitrate, or transport metadata. This avoids duplicated
security code and lets two laptops use the same external environment with
different local resource ceilings.

## High Adapter Guarantee

`lab1highadapter` is the full-resource online profile. It keeps:

- the current 30-camera Sentinel catalogue in a 50-slot holder;
- a ceiling of 30 managed external stream connections;
- up to four concurrent ephemeral preview relays;
- native advertised camera quality and media types; and
- one auto-selected live feed in the test dashboard.

The low adapter cannot overwrite this profile or reduce its assertions.

## Low Adapter Resource Contract

`lab2lowadapter` exposes the same current 30 Sentinel records but enforces four
managed external connections and one preview relay. It does not transcode,
downscale, lower bitrate, change codec, hide catalogue records, or replace
media. Resource reduction comes only from stricter local concurrency.

Switching back to high does not refresh to a different catalogue or regenerate
anything. The same durable camera identities remain visible.

## Online Playback Path

```text
live.corp8.cloud/api/ingest
        |
        v
same normalized 30-camera catalogue
        |
        +---- lab1highadapter (30 connections, 4 previews)
        |
        +---- lab2lowadapter (4 connections, 1 preview)
        |
selected exact HLS URL + cookieCheck=1
        |
ephemeral FFmpeg stream-copy
        |
dedicated no-recording MediaMTX
        |
loopback WHEP -> test dashboard
```

The relay uses no transcoding and writes no files. It receives credentials on
no URL, exposes no external locator through the dashboard API, and is limited
to a 60-second lease renewed by the active browser. Three bounded reconnects
cover transient upstream loss.

## Generated Fallback

The original generated system remains behind the `generated-fallback` Compose
profile. In that mode high keeps 50 fixtures/30 publishers and low keeps 12
records/four publishers while preserving all 50 high-quality files. GPU options
apply only to generated fixture preparation, not the online Sentinel relay.

Normal container recreation also preserves validated generated fixtures. The
guarded lab `stop` command writes a generated-only cleanup request before
Compose shutdown and then independently removes the media directory. This
avoids an update race without weakening explicit-stop cleanup.

## Durable Switching

The test dashboard writes the selected adapter to
`active-lab-adapter.json`. In online mode the selection changes local limits
without replacing the catalogue. In generated fallback, the publisher watches
the same state and reconciles its process set. The product API and main adapter
are not restarted or modified.

Activation is exact-ID and readiness-gated. The dashboard persists the profile,
validates the current shared catalogue, and restores the previous profile on a
failure. Generated fallback additionally waits for its publisher process count.

Switch requests require:

- the exact known adapter ID;
- the current environment classification (`sentinel-sandbox` online or
  `generated-only` offline); and
- a bounded `X-HCAM-Reason` value.

Invalid or malformed durable state fails closed. This online extension grants
only the exact public Sentinel sandbox catalogue and ephemeral preview path. It
does not grant credentials, private endpoints, recording, analytics, Government
data, multi-camera external scale, or deployment permission.

Online acceptance must prove the same catalogue membership under both profiles,
their exact 30/4 and 4/1 limits, native quality, zero retention, and return to
high. Generated fallback keeps its separate 50-record/30-publisher acceptance
gate; low cannot be used to claim that generated full-fidelity gate.
