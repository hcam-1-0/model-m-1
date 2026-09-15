import type { GisFeatureKind, GisLayerDefinition } from "@hcam/gis-contracts";

export function validateLayerRegistry(layers: readonly GisLayerDefinition[]): boolean {
  const ids = new Set<string>();
  return (
    layers.length > 0 &&
    layers.length <= 32 &&
    layers.every((layer) => {
      if (
        !/^[a-z][a-z0-9_]{2,31}$/.test(layer.id) ||
        ids.has(layer.id) ||
        layer.kinds.length === 0 ||
        layer.maxFeatures < 1 ||
        layer.maxFeatures > 10_000 ||
        layer.minZoom < 0 ||
        layer.minZoom > 24
      )
        return false;
      ids.add(layer.id);
      return true;
    })
  );
}
export function visibleLayers(
  layers: readonly GisLayerDefinition[],
  kinds: readonly GisFeatureKind[],
  zoom: number,
): readonly GisLayerDefinition[] {
  const requested = new Set(kinds);
  return layers.filter(
    (layer) => zoom >= layer.minZoom && layer.kinds.some((kind) => requested.has(kind)),
  );
}
