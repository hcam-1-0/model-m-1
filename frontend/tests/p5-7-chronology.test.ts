import { describe, expect, it } from "vitest";
import { p57GeneratedCases } from "../packages/quality-fixtures/src";

describe("P5.7 chronology", () => {
  it("uses one-based stable record sequence independent of locale", () => {
    expect(p57GeneratedCases[0]?.sequence).toBe(1);
    expect(p57GeneratedCases.at(-1)?.sequence).toBe(2048);
    expect(p57GeneratedCases.every((item, index) => item.sequence === index + 1)).toBe(true);
    const canonical = [...p57GeneratedCases].sort((left, right) => left.sequence - right.sequence);
    expect(canonical.map(({ ref }) => ref)).toEqual(p57GeneratedCases.map(({ ref }) => ref));
  });
});
