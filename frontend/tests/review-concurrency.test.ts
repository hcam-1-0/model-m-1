import { describe, expect, it } from "vitest";
import {
  buildReconsideration,
  checkConcurrency,
  conflictRequiresReconsideration,
} from "../packages/review-workflows/src";
import { validateReviewCommand } from "../packages/intelligence-domain/src";
const base = {
  alertRef: "SYN-ALERT-0001" as never,
  outcome: "abstain" as const,
  reasonCode: "operator_abstained",
  expectedRevision: 1,
  ifMatch: '"SYN-ETAG-1"',
  idempotencyKey: "SYN-IDEMP-ABCDEF1234",
  canonicalFingerprint: "A".repeat(64),
  policyRevision: "SYN-POLICY-007",
};
describe("P5.4 review concurrency", () => {
  it("requires strong ETag, revision, idempotency, and fingerprint", () => {
    expect(validateReviewCommand(base)).toEqual(base);
    expect(() => validateReviewCommand({ ...base, alertRef: "BAD" as never })).toThrow();
    expect(() => validateReviewCommand({ ...base, ifMatch: "weak" })).toThrow("weak_etag");
    expect(() => validateReviewCommand({ ...base, expectedRevision: 0 })).toThrow();
    expect(() => validateReviewCommand({ ...base, idempotencyKey: "bad" })).toThrow();
    expect(() => validateReviewCommand({ ...base, canonicalFingerprint: "bad" })).toThrow();
    expect(() => validateReviewCommand({ ...base, reasonCode: "free text" })).toThrow();
  });
  it("never auto-retries conflicts", () => {
    expect(checkConcurrency(base, 1, '"SYN-ETAG-1"', "A".repeat(64))).toBe("current");
    expect(checkConcurrency(base, 1, '"SYN-ETAG-2"', "A".repeat(64))).toBe("etag_mismatch");
    expect(checkConcurrency(base, 2, '"SYN-ETAG-1"', "A".repeat(64))).toBe("stale_revision");
    expect(checkConcurrency(base, 1, '"SYN-ETAG-1"', "B".repeat(64))).toBe("fingerprint_mismatch");
    expect(conflictRequiresReconsideration("current")).toBe(false);
    expect(conflictRequiresReconsideration("etag_mismatch")).toBe(true);
  });
  it("builds an explicit deterministic changed-field comparison", () => {
    expect(
      buildReconsideration({ state: "old", same: 1 }, { state: "new", same: 1 }, 1, 2),
    ).toEqual({
      priorRevision: 1,
      currentRevision: 2,
      changedFields: ["state"],
      requiresExplicitConfirmation: true,
      automaticRetry: false,
    });
  });
});
