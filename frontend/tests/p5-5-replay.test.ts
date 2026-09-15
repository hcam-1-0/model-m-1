import { describe, expect, it } from "vitest";
import {
  canonicalGeneratedJson,
  deterministicGeneratedDigest,
  generatedContractCases,
  generatedReplayManifest,
  investigationWorkloads,
} from "../packages/investigation-fixtures/src";
describe("P5.5 deterministic replay", () => {
  it("produces two identical generated-only replay digests", () => {
    const first = deterministicGeneratedDigest(generatedContractCases);
    const second = deterministicGeneratedDigest(
      JSON.parse(canonicalGeneratedJson(generatedContractCases)),
    );
    expect(first).toBe(second);
    expect(first).toBe(generatedReplayManifest.digest);
    expect(generatedReplayManifest).toMatchObject({ cases: 960, runsRequired: 2, generated: true });
  });
  it("freezes C1, C10, and C50 ceilings", () => {
    expect(Object.keys(investigationWorkloads)).toEqual(["C1", "C10", "C50"]);
    expect(investigationWorkloads.C50.timelineEntriesPerInvestigation).toBe(200);
    expect(investigationWorkloads.C50.graphNodes).toBe(100);
  });
});
