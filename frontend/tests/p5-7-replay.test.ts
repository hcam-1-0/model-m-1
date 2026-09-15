import { describe, expect, it } from "vitest";
import { p57GeneratedCases } from "../packages/quality-fixtures/src";
import { runQualityHarness, verifyCleanReplay } from "../packages/quality-harness/src";

describe("P5.7 deterministic replay", () => {
  it("produces identical clean terminal projections twice", () => {
    const first = runQualityHarness(p57GeneratedCases);
    const second = runQualityHarness(p57GeneratedCases.map((item) => ({ ...item })));
    expect(first.status).toBe("pass");
    expect(second).toEqual(first);
    expect(verifyCleanReplay(p57GeneratedCases)).toBe(true);
  });
});
