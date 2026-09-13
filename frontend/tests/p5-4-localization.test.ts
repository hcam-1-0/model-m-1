import { describe, expect, it } from "vitest";
import { catalogues, hasCompleteCatalogue } from "@hcam/i18n";
describe("P5.4 localization", () => {
  it.each(["en", "gu", "hi", "en-XA"] as const)("keeps %s catalogue complete", (locale) => {
    expect(hasCompleteCatalogue(locale)).toBe(true);
    expect(catalogues[locale]["portal.intelligence"]).toBeTruthy();
  });
});
