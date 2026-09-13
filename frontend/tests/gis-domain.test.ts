import { describe, expect, it } from "vitest";
import { asResourceId } from "@hcam/contracts";
import {
  geometryIsBounded,
  validateViewport,
  type GisAdmission,
  type GisFeatureSummary,
  type GisLayerDefinition,
} from "@hcam/gis-contracts";
import {
  clearSelection,
  clampTimeWindow,
  emptySelection,
  gisState,
  selectFeature,
  validateLayerRegistry,
  validateTimeWindow,
  visibleLayers,
} from "@hcam/gis-domain";
import { generatedGisFeatures, generatedLayers } from "@hcam/test-fixtures";

describe("shared GIS domain", () => {
  it("validates bounded viewport and geometry variants", () => {
    expect(validateViewport({ west: -1, south: -1, east: 1, north: 1, zoom: 2 })).toBe(true);
    expect(validateViewport({ west: 1, south: -1, east: -1, north: 1, zoom: 2 })).toBe(false);
    expect(validateViewport({ west: -181, south: -1, east: 1, north: 1, zoom: 2 })).toBe(false);
    expect(validateViewport(null)).toBe(false);
    expect(geometryIsBounded({ type: "Point", coordinates: [0, 0] })).toBe(true);
    expect(
      geometryIsBounded({
        type: "LineString",
        coordinates: [
          [0, 0],
          [1, 1],
        ],
      }),
    ).toBe(true);
    expect(
      geometryIsBounded({
        type: "Polygon",
        coordinates: [
          [
            [0, 0],
            [1, 0],
            [0, 0],
          ],
        ],
      }),
    ).toBe(true);
    expect(geometryIsBounded({ type: "Point", coordinates: [200, 0] })).toBe(false);
  });
  it("validates layer uniqueness and visibility", () => {
    const layers = generatedLayers as readonly GisLayerDefinition[];
    expect(validateLayerRegistry(layers)).toBe(true);
    expect(validateLayerRegistry([])).toBe(false);
    expect(validateLayerRegistry([...layers, layers[0]!])).toBe(false);
    expect(validateLayerRegistry([{ ...layers[0]!, id: "BAD" }])).toBe(false);
    expect(validateLayerRegistry([{ ...layers[0]!, kinds: [] }])).toBe(false);
    expect(validateLayerRegistry([{ ...layers[0]!, maxFeatures: 10001 }])).toBe(false);
    expect(validateLayerRegistry([{ ...layers[0]!, minZoom: 25 }])).toBe(false);
    expect(visibleLayers(layers, ["camera"], 0).map((item) => item.id)).toEqual(["camera_status"]);
  });
  it("keeps selection bounded and revisioned", () => {
    const ids = Array.from({ length: 55 }, (_, index) =>
      asResourceId(`SYN-ID-${String(index).padStart(4, "0")}`)!,
    );
    let state = emptySelection;
    for (const id of ids) state = selectFeature(state, id, true);
    expect(state.selected).toHaveLength(50);
    expect(state.focused).toBe(ids[54]);
    state = selectFeature(state, ids[0]!, false);
    expect(state.selected).toEqual([ids[0]]);
    expect(clearSelection(state)).toMatchObject({ selected: [], focused: null });
  });
  it("validates and clamps UTC time windows", () => {
    const valid = {
      from: "2026-09-07T23:00:00.000Z",
      to: "2026-09-08T00:00:00.000Z",
      serverNow: "2026-09-08T00:20:00.000Z",
    };
    expect(validateTimeWindow(valid)).toBe(true);
    expect(validateTimeWindow({ ...valid, to: "2026-09-09T00:00:00.000Z" })).toBe(false);
    expect(validateTimeWindow({ ...valid, from: "bad" })).toBe(false);
    const clamped = clampTimeWindow({
      from: "2026-09-01T00:00:00.000Z",
      to: "2026-09-09T00:00:00.000Z",
      serverNow: valid.serverNow,
    });
    expect(Date.parse(clamped.to)).toBe(Date.parse(valid.serverNow));
    expect(Date.parse(clamped.to) - Date.parse(clamped.from)).toBe(86_400_000);
  });
  it("projects truthful GIS UI states", () => {
    const base = generatedGisFeatures(2) as readonly GisFeatureSummary[];
    const map: GisAdmission = {
      admitted: true,
      mode: "maplibre",
      reason: "requested",
      listFallback: true,
    };
    expect(gisState(null, map, new Date())).toBe("loading");
    expect(gisState([], map, new Date())).toBe("empty");
    expect(gisState(base, map, new Date("2026-09-08T00:20:00Z"))).toBe("unknown");
    const current = base.map((item) => ({ ...item, status: "available" as const }));
    expect(gisState(current, map, new Date("2026-09-08T02:00:00Z"))).toBe("stale");
    expect(
      gisState(
        current,
        { ...map, admitted: false, mode: "list_only" },
        new Date("2026-09-08T00:20:00Z"),
      ),
    ).toBe("degraded");
    expect(gisState(current, map, new Date("2026-09-08T00:20:00Z"))).toBe("ready");
  });
});
