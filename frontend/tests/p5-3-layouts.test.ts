import { describe, expect, it } from "vitest";
import { updateLayout, validateLayout } from "@hcam/camera-live-domain";
import { generatedLayout } from "@hcam/test-fixtures";

describe("P5.3 layouts", () => {
  it("accepts generated layouts with unique tiles", () => {
    const layout = generatedLayout(4);
    expect(validateLayout(layout)).toBe(true);
    expect(validateLayout({ ...layout, tiles: [...layout.tiles, layout.tiles[0]!] })).toBe(false);
    expect(validateLayout({ ...layout, id: "invalid" })).toBe(false);
    expect(validateLayout({ ...layout, revision: 0 })).toBe(false);
    expect(validateLayout({ ...layout, columns: 5 as 1 })).toBe(false);
    expect(
      validateLayout({ ...layout, tiles: Array.from({ length: 11 }, () => layout.tiles[0]!) }),
    ).toBe(false);
    expect(
      validateLayout({ ...layout, tiles: [{ tileId: "invalid", streamId: null, order: 0 }] }),
    ).toBe(false);
    expect(
      validateLayout({
        ...layout,
        tiles: [{ tileId: "SYN-TILE-001", streamId: "invalid", order: 0 }],
      }),
    ).toBe(false);
    expect(
      validateLayout({ ...layout, tiles: [{ tileId: "SYN-TILE-001", streamId: null, order: -1 }] }),
    ).toBe(false);
  });
  it("uses revision and ETag concurrency", () => {
    const current = generatedLayout(4);
    const next = { ...current, columns: 3 as const, revision: 2, etag: "SYN-ETAG-0002" };
    expect(updateLayout(current, current.etag, next).accepted).toBe(true);
    expect(updateLayout(current, "SYN-STALE-ETAG", next)).toEqual({
      accepted: false,
      layout: current,
    });
    expect(updateLayout(current, current.etag, { ...next, revision: 3 }).accepted).toBe(false);
    expect(updateLayout(current, current.etag, { ...next, id: "invalid" }).accepted).toBe(false);
  });
});
