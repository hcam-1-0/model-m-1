export interface WorkspaceTile {
  readonly tileId: string;
  readonly streamId: string | null;
  readonly order: number;
}
export interface WorkspaceLayout {
  readonly id: string;
  readonly name: string;
  readonly revision: number;
  readonly etag: string;
  readonly columns: 1 | 2 | 3 | 4;
  readonly tiles: readonly WorkspaceTile[];
  readonly generated: true;
}
const safeReference = /^SYN-[A-Z0-9-]{3,48}$/u;
export function validateLayout(layout: WorkspaceLayout): boolean {
  if (!safeReference.test(layout.id) || layout.revision < 1 || layout.tiles.length > 10)
    return false;
  if (![1, 2, 3, 4].includes(layout.columns)) return false;
  const ids = new Set(layout.tiles.map((tile) => tile.tileId));
  const orders = new Set(layout.tiles.map((tile) => tile.order));
  return (
    ids.size === layout.tiles.length &&
    orders.size === layout.tiles.length &&
    layout.tiles.every(
      (tile) =>
        safeReference.test(tile.tileId) &&
        (tile.streamId === null || safeReference.test(tile.streamId)) &&
        Number.isInteger(tile.order) &&
        tile.order >= 0,
    )
  );
}
export function updateLayout(
  current: WorkspaceLayout,
  expectedEtag: string,
  next: WorkspaceLayout,
): { readonly accepted: boolean; readonly layout: WorkspaceLayout } {
  if (
    current.etag !== expectedEtag ||
    next.revision !== current.revision + 1 ||
    !validateLayout(next)
  )
    return { accepted: false, layout: current };
  return { accepted: true, layout: next };
}
