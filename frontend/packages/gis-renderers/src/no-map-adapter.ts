import type { ResourceId } from "@hcam/contracts";
import {
  validateViewport,
  type GisAdapter,
  type GisFeatureSummary,
  type GisViewport,
} from "@hcam/gis-contracts";

export function createListAdapter(features: readonly GisFeatureSummary[]): GisAdapter {
  let disposed = false;
  return {
    kind: "list_only",
    admit: () => ({ admitted: true, mode: "list_only", reason: "requested", listFallback: true }),
    list: (viewport: GisViewport) =>
      Promise.resolve(!disposed && validateViewport(viewport) ? features : []),
    focus: (id: ResourceId) =>
      Promise.resolve(!disposed && features.some((feature) => feature.id === id)),
    dispose: () => {
      disposed = true;
    },
  };
}
