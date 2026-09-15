import { describe, expect, it } from "vitest";
import { findProhibitedFields, validateGeneratedCase } from "../packages/quality-domain/src";
import { p57GeneratedCases } from "../packages/quality-fixtures/src";

describe("P5.7 security and generated-data boundary", () => {
  it("rejects prohibited evidence keys recursively", () => {
    expect(findProhibitedFields({ safe: [{ display: "generated" }] })).toEqual([]);
    expect(
      findProhibitedFields({ nested: { access_token: "not-retained", camera_locator: "x" } }),
    ).toEqual(["$.nested.access_token", "$.nested.camera_locator"]);
  });

  it("rejects non-generated and authority-invalid cases", () => {
    const valid = p57GeneratedCases[0];
    if (!valid) throw new Error("fixture_missing");
    expect(validateGeneratedCase(valid).status).toBe("pass");
    expect(validateGeneratedCase({ ...valid, generatedOnly: false }).reason).toBe(
      "generated_boundary_breached",
    );
    expect(validateGeneratedCase({ ...valid, authority: "mandatory_review" }).reason).toBe(
      "authority_changed",
    );
  });
});
