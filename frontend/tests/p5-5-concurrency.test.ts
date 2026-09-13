import { describe, expect, it } from "vitest";
import { authorizeGeneratedMutation } from "../packages/investigation-domain/src";
describe("P5.5 concurrency", () => {
  const envelope = {
    revision: 7,
    etag: '"SYN-ETAG-7"',
    idempotencyKey: "SYN-IDEMP-ABCDEF12",
    deliberateReconsideration: false,
  };
  it("requires revision, ETag, idempotency, and deliberate conflict reconsideration", () => {
    expect(authorizeGeneratedMutation(envelope, 7, envelope.etag).allowed).toBe(true);
    expect(
      authorizeGeneratedMutation({ ...envelope, revision: 6 }, 7, envelope.etag),
    ).toMatchObject({ allowed: false, reason: "stale_revision" });
    expect(
      authorizeGeneratedMutation({ ...envelope, etag: '"OLD"' }, 7, envelope.etag),
    ).toMatchObject({ allowed: false, reason: "etag_mismatch" });
    expect(
      authorizeGeneratedMutation({ ...envelope, idempotencyKey: "bad" }, 7, envelope.etag),
    ).toMatchObject({ allowed: false, reason: "invalid_idempotency" });
    expect(authorizeGeneratedMutation(envelope, 7, envelope.etag, true)).toMatchObject({
      allowed: false,
      reason: "reconsideration_required",
    });
    expect(
      authorizeGeneratedMutation(
        { ...envelope, deliberateReconsideration: true },
        7,
        envelope.etag,
        true,
      ).allowed,
    ).toBe(true);
  });
});
