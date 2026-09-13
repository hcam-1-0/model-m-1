import { describe, expect, it } from "vitest";
import { MemoryReviewDrafts } from "../packages/review-workflows/src";
describe("P5.4 review drafts", () => {
  it.each([
    "logout",
    "department_switch",
    "role_loss",
    "expiry",
    "route_disposal",
    "window_close",
  ] as const)("purges memory-only drafts on %s", (reason) => {
    const drafts = new MemoryReviewDrafts();
    drafts.set({
      alertRef: "SYN-ALERT-0001",
      outcome: null,
      reasonCode: "",
      createdAt: "2026-09-09T09:00:00Z",
    });
    expect(drafts.size).toBe(1);
    expect(drafts.get("SYN-ALERT-0001")).not.toBeNull();
    expect(drafts.get("SYN-ALERT-OTHER")).toBeNull();
    expect(drafts.purge(reason)).toBe(1);
    expect(drafts.size).toBe(0);
    expect(drafts.lastPurgeReason).toBe(reason);
  });
});
