import { describe, expect, it } from "vitest";
import { p56InvalidationBatch } from "@hcam/event-invalidation";
describe("P5.6 event invalidation", () => {
  it("treats events as hints requiring HTTP confirmation", () => {
    expect(p56InvalidationBatch("administrationChanged", 9)).toMatchObject({
      highestSequence: 9,
      requiresHttpConfirmation: true,
    });
    expect(p56InvalidationBatch("securityProjectionChanged", 10).queryScopes).toContain(
      "security.audit",
    );
  });
});
