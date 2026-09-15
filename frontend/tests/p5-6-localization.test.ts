import { describe, expect, it } from "vitest";
import { baseMessages, hasCompleteCatalogue } from "@hcam/i18n";
describe("P5.6 localization projection", () => {
  it("provides English Gujarati and Hindi operator labels", () => {
    for (const locale of ["en", "gu", "hi"] as const) {
      expect(hasCompleteCatalogue(locale)).toBe(true);
    }
    expect(baseMessages["administration.overview"]).toBeTruthy();
    expect(baseMessages["security.assurance"]).toBeTruthy();
    expect(baseMessages["operations.platform"]).toBeTruthy();
  });
});
