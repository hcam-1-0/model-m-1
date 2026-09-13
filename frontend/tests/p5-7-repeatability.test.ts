import { describe, expect, it } from "vitest";
import { deterministicDigest } from "../packages/quality-domain/src";
import { generateQualityCases } from "../packages/quality-fixtures/src";
import { runQualityHarness } from "../packages/quality-harness/src";

describe("P5.7 exact local repeatability", () => {
  it("regenerates the same source corpus and terminal digest", () => {
    const first = generateQualityCases();
    const second = generateQualityCases();
    expect(deterministicDigest(first)).toBe(deterministicDigest(second));
    expect(runQualityHarness(first).terminalDigest).toBe(runQualityHarness(second).terminalDigest);
  });
});
