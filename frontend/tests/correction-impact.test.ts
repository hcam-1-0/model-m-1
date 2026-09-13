import { describe, expect, it } from "vitest";
import { correctionImpact } from "../packages/intelligence-domain/src";
describe("P5.4 corrections", () => {
  it("deduplicates bounded impact and never rewrites history", () => {
    const value = correctionImpact("SYN-CORRECTION-0001" as never, "SYN-ALERT-0001" as never, [
      "SYN-ALERT-0001" as never,
      "SYN-ALERT-0001" as never,
    ]);
    expect(value.impactedRefs).toHaveLength(1);
    expect(value.mutationDisabled).toBe(true);
    expect(value.requiresRefetch).toBe(true);
    expect(value.historyRewritten).toBe(false);
  });
});
