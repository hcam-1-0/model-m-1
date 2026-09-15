import type { GisFeatureSummary, GisRendererMode } from "@hcam/gis-contracts";

export async function createDeckOverlay(
  features: readonly GisFeatureSummary[],
  mode: Extract<GisRendererMode, "deck_overlaid" | "deck_interleaved">,
): Promise<unknown> {
  const [{ MapboxOverlay }, { ScatterplotLayer }] = await Promise.all([
    import("@deck.gl/mapbox"),
    import("@deck.gl/layers"),
  ]);
  const points = features.filter((feature) => feature.geometry.type === "Point");
  return new MapboxOverlay({
    interleaved: mode === "deck_interleaved",
    layers: [
      new ScatterplotLayer<GisFeatureSummary>({
        id: "hcam-generated-points",
        data: points,
        getPosition: (item): [number, number] =>
          item.geometry.type === "Point" ? [...item.geometry.coordinates] : [0, 0],
        getRadius: 1200,
        radiusMinPixels: 4,
        radiusMaxPixels: 12,
        getFillColor: (item) =>
          item.severity === "critical"
            ? [180, 35, 24, 190]
            : item.severity === "attention"
              ? [154, 90, 0, 180]
              : [8, 124, 120, 170],
        pickable: false,
      }),
    ],
  });
}
