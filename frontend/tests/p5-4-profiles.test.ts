import { describe, expect, it } from "vitest";
import {
  intelligenceProfiles,
  limitsForIntelligenceProfile,
} from "../packages/intelligence-domain/src";
describe("P5.4 resource profiles", () => {
  it("changes rendering capacity but never authority", () => {
    const limits = intelligenceProfiles.map(limitsForIntelligenceProfile);
    expect(limits.map((item) => item.authorityChanged)).toEqual([
      false,
      false,
      false,
      false,
      false,
    ]);
    expect(limits[0]).toMatchObject({
      queuePageSize: 10,
      graphNodes: 12,
      graphEdges: 24,
      motion: "reduced",
    });
    expect(limits.at(-1)).toMatchObject({ queuePageSize: 50, graphNodes: 100, graphEdges: 200 });
  });
});
