import { describe, expect, it } from "vitest";
import { catalogues, hasCompleteCatalogue, locales } from "@hcam/i18n";

describe("P5.3 localization", () => {
  it.each(locales)("keeps %s catalogue complete", (locale) =>
    expect(hasCompleteCatalogue(locale)).toBe(true),
  );
  it("keeps generated safety language available", () =>
    expect(catalogues.en["shell.generated"]).toContain("Generated"));
});
