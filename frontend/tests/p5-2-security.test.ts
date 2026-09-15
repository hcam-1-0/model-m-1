import { describe, expect, it, vi } from "vitest";
import {
  createDeckOverlay,
  createListAdapter,
  providerRuntimeAllowed,
  generatedLocalStyle,
  isLocalGeneratedStyle,
  mountMapLibre,
  toGeneratedFeatureCollection,
  validateDisabledProvider,
} from "@hcam/gis-renderers";
import { generatedGisFeatures } from "@hcam/test-fixtures";
import type { GisFeatureSummary } from "@hcam/gis-contracts";
import { validateViewport } from "@hcam/gis-contracts";
import { parseSessionProjection } from "@hcam/contracts";
import { p52GeneratedReadPolicies } from "@hcam/query-policy";
import { validateSignal } from "@hcam/observability";
import { generatedSession } from "@hcam/test-fixtures";
const mapState = vi.hoisted(
  (): {
    last: null | {
      removed: boolean;
      zoom: number;
      eased: unknown;
      fitted: unknown;
      controls: number;
    };
    clickValue: unknown;
  } => ({
    last: null,
    clickValue: "SYN-GEO-0001",
  }),
);
vi.mock("maplibre-gl", () => ({
  Map: class {
    removed = false;
    zoom = 2;
    eased: unknown = null;
    fitted: unknown = null;
    controls = 0;
    constructor() {
      mapState.last = this;
    }
    addControl() {
      this.controls += 1;
    }
    once(_event: string, callback: () => void) {
      callback();
    }
    on(
      _event: string,
      _layer: string,
      callback: (event: {
        features?: readonly { properties?: Readonly<Record<string, unknown>> }[];
      }) => void,
    ) {
      callback({ features: [{ properties: { id: mapState.clickValue } }] });
      return this;
    }
    getZoom() {
      return this.zoom;
    }
    easeTo(value: unknown) {
      this.eased = value;
    }
    fitBounds(value: unknown) {
      this.fitted = value;
    }
    remove() {
      this.removed = true;
    }
  },
  NavigationControl: class {
    readonly generated = true;
  },
}));
vi.mock("@deck.gl/mapbox", () => ({
  MapboxOverlay: class {
    constructor(readonly options: unknown) {}
  },
}));
vi.mock("@deck.gl/layers", () => ({
  ScatterplotLayer: class {
    constructor(
      readonly options: {
        data: readonly GisFeatureSummary[];
        getPosition: (item: GisFeatureSummary) => readonly [number, number];
        getFillColor: (item: GisFeatureSummary) => readonly number[];
      },
    ) {
      for (const item of options.data) {
        options.getPosition(item);
        options.getFillColor(item);
      }
      options.getPosition({
        ...options.data[0]!,
        geometry: { type: "LineString", coordinates: [] },
      });
    }
  },
}));
describe("P5.2 security boundaries", () => {
  it("accepts exact disabled HTTPS provider metadata but never enables runtime", () => {
    const provider = {
      id: "future-tiles",
      enabled: false as const,
      destination: "https://tiles.invalid/",
      purpose: "Future exact destination contract",
    };
    expect(validateDisabledProvider(provider)).toBe(true);
    expect(providerRuntimeAllowed()).toBe(false);
    expect(validateDisabledProvider({ ...provider, id: "BAD" })).toBe(false);
    expect(validateDisabledProvider({ ...provider, destination: "http://tiles.invalid/" })).toBe(
      false,
    );
    expect(
      validateDisabledProvider({ ...provider, destination: "https://user:pass@tiles.invalid/" }),
    ).toBe(false);
    expect(
      validateDisabledProvider({ ...provider, destination: "https://tiles.invalid/path" }),
    ).toBe(false);
    expect(validateDisabledProvider({ ...provider, destination: "bad" })).toBe(false);
    expect(validateDisabledProvider({ ...provider, purpose: "x" })).toBe(false);
  });
  it("creates only local generated styles", () => {
    const features = generatedGisFeatures(2) as readonly GisFeatureSummary[];
    const collection = toGeneratedFeatureCollection(features);
    expect(collection.features).toHaveLength(2);
    const style = generatedLocalStyle(features);
    expect(isLocalGeneratedStyle(style)).toBe(true);
    expect(isLocalGeneratedStyle({ ...style, name: "https://external.invalid" })).toBe(false);
  });
  it("keeps list adapter usable and disposable", async () => {
    const features = generatedGisFeatures(2) as readonly GisFeatureSummary[];
    const adapter = createListAdapter(features);
    const viewport = { west: -1, south: -1, east: 1, north: 1, zoom: 2 };
    expect(adapter.admit().mode).toBe("list_only");
    expect(await adapter.list(viewport)).toHaveLength(2);
    expect(await adapter.list({ ...viewport, zoom: 100 })).toEqual([]);
    expect(await adapter.focus(features[0]!.id)).toBe(true);
    adapter.dispose();
    expect(await adapter.list(viewport)).toEqual([]);
    expect(await adapter.focus(features[0]!.id)).toBe(false);
  });
  it("mounts, focuses, and disposes the generated MapLibre adapter", () => {
    const features = generatedGisFeatures(2) as readonly GisFeatureSummary[];
    const selected: string[] = [];
    mapState.clickValue = features[0]!.id;
    const controller = mountMapLibre(document.createElement("div"), features, (id) =>
      selected.push(id),
    );
    expect(selected).toEqual([features[0]!.id]);
    expect(mapState.last?.controls).toBe(1);
    expect(controller.fit()).toBe(true);
    expect(mapState.last?.fitted).not.toBeNull();
    expect(controller.focus(features[0]!.id)).toBe(true);
    expect(mapState.last?.eased).not.toBeNull();
    expect(controller.focus("SYN-MISSING-0001" as never)).toBe(false);
    controller.dispose();
    expect(mapState.last?.removed).toBe(true);

    mapState.clickValue = null;
    mountMapLibre(document.createElement("div"), features, (id) => selected.push(id)).dispose();
    expect(selected).toEqual([features[0]!.id]);
    const empty = mountMapLibre(document.createElement("div"), [], () => undefined);
    expect(empty.fit()).toBe(false);
    empty.dispose();
  });
  it("constructs both optional deck.gl modes", async () => {
    const features = generatedGisFeatures(12) as readonly GisFeatureSummary[];
    await expect(createDeckOverlay(features, "deck_overlaid")).resolves.toBeDefined();
    await expect(createDeckOverlay(features, "deck_interleaved")).resolves.toBeDefined();
  });
  it("keeps reads bounded and signals low-cardinality", () => {
    expect(Object.values(p52GeneratedReadPolicies).every((policy) => policy.retryLimit === 1)).toBe(
      true,
    );
    expect(
      validateSignal({
        name: "gis_fallback",
        portal: "command",
        routeClass: "generated_gis",
        state: "degraded",
        outcome: "ok",
        durationBucket: "lt100",
      }),
    ).toBe(true);
  });
  it("rejects malformed, non-finite, extra, and inverted viewports", () => {
    const viewport = { west: -1, south: -1, east: 1, north: 1, zoom: 2 };
    expect(validateViewport(viewport)).toBe(true);
    for (const invalid of [
      null,
      [],
      { ...viewport, extra: true },
      { ...viewport, zoom: Number.NaN },
      { ...viewport, zoom: "2" },
      { ...viewport, west: -181 },
      { ...viewport, south: -91 },
      { ...viewport, east: 181 },
      { ...viewport, north: 91 },
      { ...viewport, zoom: 25 },
      { ...viewport, west: 1, east: -1 },
      { ...viewport, south: 1, north: -1 },
    ]) {
      expect(validateViewport(invalid)).toBe(false);
    }
  });
  it("keeps strict session validation CSP compatible", () => {
    const session = generatedSession();
    expect(parseSessionProjection(session)).toEqual(session);
    for (const invalid of [
      [],
      { ...session, extra: true },
      { ...session, operatorRef: "short" },
      { ...session, sessionRef: "short" },
      { ...session, department: null },
      { ...session, department: { ...session.department, extra: true } },
      { ...session, departments: [] },
      { ...session, departments: Array.from({ length: 33 }, () => session.department) },
      { ...session, capabilities: ["administrator", "administrator"] },
      { ...session, policyRevision: "" },
      { ...session, serverTime: "not-a-timestamp" },
      { ...session, staleAt: "not-a-timestamp" },
      { ...session, expiresAt: "not-a-timestamp" },
      { ...session, reauthenticationRequired: "false" },
      { ...session, csrfToken: "short" },
      { ...session, locale: "fr" },
      { ...session, timezone: "" },
    ]) {
      expect(parseSessionProjection(invalid)).toBeNull();
    }
  });
});
