const cursorPattern = /^SYN-P55-CURSOR-(\d{1,6})$/u;
export function encodeStableCursor(offset: number): string {
  if (!Number.isSafeInteger(offset) || offset < 0 || offset > 100_000)
    throw new Error("invalid_cursor_offset");
  return `SYN-P55-CURSOR-${offset}`;
}
export function decodeStableCursor(cursor: string | null): number {
  if (cursor === null) return 0;
  const match = cursorPattern.exec(cursor);
  if (!match) throw new Error("invalid_stable_cursor");
  return Number(match[1]);
}
export function stablePage<T>(
  items: readonly T[],
  cursor: string | null,
  limit: 10 | 25 | 50,
): { readonly items: readonly T[]; readonly nextCursor: string | null } {
  const offset = decodeStableCursor(cursor);
  const page = items.slice(offset, offset + limit);
  return {
    items: page,
    nextCursor:
      offset + page.length < items.length ? encodeStableCursor(offset + page.length) : null,
  };
}
