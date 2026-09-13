import type { StyleSpecification } from "maplibre-gl";
import type { GisFeatureSummary } from "@hcam/gis-contracts";

export interface GeneratedFeatureCollection {
  readonly type: "FeatureCollection";
  readonly features: readonly {
    readonly type: "Feature";
    readonly id: string;
    readonly geometry: GisFeatureSummary["geometry"];
    readonly properties: Readonly<Record<string, string | boolean>>;
  }[];
}
export function toGeneratedFeatureCollection(
  features: readonly GisFeatureSummary[],
): GeneratedFeatureCollection {
  return {
    type: "FeatureCollection",
    features: features.map((feature) => ({
      type: "Feature",
      id: feature.id,
      geometry: feature.geometry,
      properties: {
        id: feature.id,
        label: feature.label,
        kind: feature.kind,
        status: feature.status,
        severity: feature.severity,
        generated: true,
      },
    })),
  };
}
export function generatedLocalStyle(features: readonly GisFeatureSummary[]): StyleSpecification {
  return {
    version: 8,
    name: "HCAM generated local style",
    sources: {
      generated: { type: "geojson", data: toGeneratedFeatureCollection(features) as never },
    },
    layers: [
      { id: "generated-background", type: "background", paint: { "background-color": "#e8edef" } },
      {
        id: "generated-polygon",
        type: "fill",
        source: "generated",
        filter: ["==", ["geometry-type"], "Polygon"],
        paint: { "fill-color": "#27817d", "fill-opacity": 0.18 },
      },
      {
        id: "generated-line",
        type: "line",
        source: "generated",
        filter: ["==", ["geometry-type"], "LineString"],
        paint: { "line-color": "#1c64a8", "line-width": 3 },
      },
      {
        id: "generated-points",
        type: "circle",
        source: "generated",
        filter: ["==", ["geometry-type"], "Point"],
        paint: {
          "circle-color": [
            "match",
            ["get", "severity"],
            "critical",
            "#b42318",
            "attention",
            "#9a5a00",
            "#087c78",
          ],
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 0, 5, 8, 9],
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 2,
        },
      },
    ],
  };
}
export function isLocalGeneratedStyle(style: StyleSpecification): boolean {
  const serialized = JSON.stringify(style);
  return (
    !/(https?:|mapbox:|pmtiles:|file:|ftp:|data:)/i.test(serialized) &&
    serialized.includes("HCAM generated local style")
  );
}
