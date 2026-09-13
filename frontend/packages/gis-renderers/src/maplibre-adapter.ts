import { Map, NavigationControl, type Map as MapLibreMap } from "maplibre-gl";
import type { ResourceId } from "@hcam/contracts";
import type { GisFeatureSummary } from "@hcam/gis-contracts";
import { generatedLocalStyle } from "./style-policy";

export interface MapLibreController {
  readonly map: MapLibreMap;
  focus(id: ResourceId): boolean;
  fit(): boolean;
  dispose(): void;
}
export function mountMapLibre(
  container: HTMLElement,
  features: readonly GisFeatureSummary[],
  onSelect: (id: ResourceId) => void,
): MapLibreController {
  const points = features.filter(
    (
      feature,
    ): feature is GisFeatureSummary & {
      readonly geometry: Extract<GisFeatureSummary["geometry"], { readonly type: "Point" }>;
    } => feature.geometry.type === "Point",
  );
  const coordinates = points.map((feature) => feature.geometry.coordinates);
  const totals = coordinates.reduce<[number, number]>(
    ([x, y], [nextX, nextY]) => [x + nextX, y + nextY],
    [0, 0],
  );
  const center: [number, number] = coordinates.length
    ? [totals[0] / coordinates.length, totals[1] / coordinates.length]
    : [0, 0];
  const fit = () => {
    if (coordinates.length === 0) return false;
    const xs = coordinates.map(([x]) => x);
    const ys = coordinates.map(([, y]) => y);
    map.fitBounds(
      [
        [Math.min(...xs), Math.min(...ys)],
        [Math.max(...xs), Math.max(...ys)],
      ],
      { padding: 40, duration: 0, maxZoom: 12 },
    );
    return true;
  };
  const map = new Map({
    container,
    style: generatedLocalStyle(features),
    center,
    zoom: coordinates.length ? 8 : 2,
    minZoom: 0,
    maxZoom: 16,
    attributionControl: false,
    cooperativeGestures: true,
    fadeDuration: 0,
  });
  map.addControl(new NavigationControl({ showCompass: false }), "top-right");
  map.once("load", () => {
    fit();
    map.on(
      "click",
      "generated-points",
      (event: {
        readonly features?: readonly { readonly properties?: Readonly<Record<string, unknown>> }[];
      }) => {
        const id = event.features?.[0]?.properties?.id;
        if (typeof id === "string") onSelect(id as ResourceId);
      },
    );
  });
  return {
    map,
    focus: (id) => {
      const feature = points.find((item) => item.id === id);
      if (feature?.geometry.type !== "Point") return false;
      map.easeTo({
        center: [...feature.geometry.coordinates],
        zoom: Math.max(map.getZoom(), 5),
        duration: 0,
      });
      return true;
    },
    fit,
    dispose: () => map.remove(),
  };
}
