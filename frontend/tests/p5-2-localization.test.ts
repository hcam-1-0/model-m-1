import { describe, expect, it } from "vitest";
import { baseMessages, catalogues, hasCompleteCatalogue, locales } from "@hcam/i18n";
describe("P5.2 localization", () => {
  it("keeps every catalogue structurally complete", () => {
    for (const locale of locales) expect(hasCompleteCatalogue(locale)).toBe(true);
    expect(Object.keys(catalogues.gu)).toEqual(Object.keys(baseMessages));
    expect(Object.keys(catalogues.hi)).toEqual(Object.keys(baseMessages));
  });
  it("has localized GIS and truth states", () => {
    expect(catalogues.gu["portal.gis"]).not.toBe(baseMessages["portal.gis"]);
    expect(catalogues.hi["state.unknown"]).not.toBe(baseMessages["state.unknown"]);
    expect(catalogues["en-XA"]["portal.gis"]).toContain("[!!");
  });
});
