import { afterEach, describe, expect, it } from "vitest";
import { findProhibitedFields } from "../packages/quality-domain/src";

describe("P5.7 browser storage and redaction", () => {
  afterEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  it("retains only non-sensitive presentation preferences", () => {
    localStorage.setItem("hcam.resource-profile", "R01");
    sessionStorage.setItem("hcam.locale", "gu-IN");
    const projection = {
      local: Object.fromEntries(Object.entries(localStorage)),
      session: Object.fromEntries(Object.entries(sessionStorage)),
    };
    expect(findProhibitedFields(projection)).toEqual([]);
    expect(JSON.stringify(projection)).not.toMatch(/token|secret|credential|identity|media_url/iu);
  });
});
