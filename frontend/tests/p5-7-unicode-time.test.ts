import { describe, expect, it } from "vitest";
import { hostileUnicodeFixtures } from "../packages/quality-fixtures/src";
import { canonicalize, deterministicDigest } from "../packages/quality-domain/src";

describe("P5.7 Unicode and canonical time", () => {
  it("retains bounded Unicode display fixtures while canonical ordering stays stable", () => {
    expect(hostileUnicodeFixtures).toHaveLength(5);
    expect(hostileUnicodeFixtures.every((value) => value.length <= 64)).toBe(true);
    const left = { z: "2026-09-12T06:30:00.000Z", a: hostileUnicodeFixtures };
    const right = { a: hostileUnicodeFixtures, z: "2026-09-12T06:30:00.000Z" };
    expect(canonicalize(left)).toBe(canonicalize(right));
    expect(deterministicDigest(left)).toBe(deterministicDigest(right));
  });
});
