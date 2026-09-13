import type { ResourceId } from "@hcam/contracts";
import type { GisSelection } from "@hcam/gis-contracts";

export const emptySelection: GisSelection = { selected: [], focused: null, revision: 0 };
export function selectFeature(state: GisSelection, id: ResourceId, additive = false): GisSelection {
  const selected = additive ? [...new Set([...state.selected, id])].slice(-50) : [id];
  return { selected, focused: id, revision: state.revision + 1 };
}
export function clearSelection(state: GisSelection): GisSelection {
  return { selected: [], focused: null, revision: state.revision + 1 };
}
