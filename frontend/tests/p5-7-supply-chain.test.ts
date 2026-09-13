import { describe, expect, it } from "vitest";
import { generatedQualityManifest } from "../packages/quality-fixtures/src";

describe("P5.7 supply-chain claim boundary", () => {
  it("labels the generated corpus without claiming independent provenance", () => {
    expect(generatedQualityManifest.generatedOnly).toBe(true);
    expect(generatedQualityManifest.exactCaseCount).toBe(2048);
    expect(generatedQualityManifest).not.toHaveProperty("slsaLevel");
    expect(generatedQualityManifest).not.toHaveProperty("independentlyReproducible");
  });
});
