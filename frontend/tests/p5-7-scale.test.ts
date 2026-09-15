import { describe, expect, it } from "vitest";
import { workloadProfiles } from "../packages/quality-contracts/src";
import { p57GeneratedCases } from "../packages/quality-fixtures/src";

describe("P5.7 C1/C10/C50 generated workflow scale", () => {
  it("covers every workload deterministically without making a capacity claim", () => {
    const counts = Object.fromEntries(
      workloadProfiles.map((workload) => [
        workload,
        p57GeneratedCases.filter((item) => item.workload === workload).length,
      ]),
    );
    expect(Object.values(counts).reduce((total, count) => total + count, 0)).toBe(2048);
    expect(counts.C1).toBeGreaterThan(680);
    expect(counts.C10).toBeGreaterThan(680);
    expect(counts.C50).toBeGreaterThan(680);
  });
});
