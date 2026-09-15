import { describe, expect, it } from "vitest";
import {
  generatedQueue,
  generatedRelationship,
  generatedRuleTrace,
} from "../packages/intelligence-fixtures/src";
describe("P5.4 deterministic replay", () => {
  it("produces identical canonical generated projections twice", () => {
    const replay = () =>
      JSON.stringify({
        queue: generatedQueue("mandatory_review", 50),
        relationship: generatedRelationship(50),
        trace: generatedRuleTrace(),
      });
    expect(replay()).toBe(replay());
  });
});
