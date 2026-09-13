import { describe, expect, it } from "vitest";
import { conflictRecovery, resolveConcurrency } from "../packages/governance-domain/src";
const base = {
  expectedEtag: '"A"',
  actualEtag: '"A"',
  expectedRevision: 2,
  actualRevision: 2,
  idempotencyKey: "SYN-IDEMP-CHANGE-0001",
  existingReceiptKey: null,
};
describe("P5.6 concurrency", () => {
  it("requires ETag, revision, and bounded idempotency", () => {
    expect(resolveConcurrency(base)).toBe("proceed");
    expect(resolveConcurrency({ ...base, actualEtag: '"B"' })).toBe("etag_mismatch");
    expect(resolveConcurrency({ ...base, actualRevision: 3 })).toBe("stale_revision");
    expect(resolveConcurrency({ ...base, existingReceiptKey: base.idempotencyKey })).toBe("replay");
    expect(resolveConcurrency({ ...base, idempotencyKey: "bad" })).toBe("idempotency_conflict");
  });
  it("never retries a stale mutation automatically", () => {
    expect(conflictRecovery).toEqual({
      automaticRetry: false,
      requiresRefetch: true,
      requiresComparison: true,
      requiresDeliberateReconsideration: true,
    });
  });
});
