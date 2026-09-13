import { describe, expect, it } from "vitest";
import {
  p56ContractCases,
  scanGeneratedProjection,
} from "../packages/admin-security-operations-fixtures/src";
import { validateAdministrationSignal } from "@hcam/observability";
describe("P5.6 security boundary", () => {
  it("finds no forbidden generated fields", () => {
    expect(scanGeneratedProjection(p56ContractCases)).toEqual([]);
    expect(scanGeneratedProjection({ password: "bad" })).not.toEqual([]);
  });
  it("accepts low-cardinality sanitized signals only", () => {
    expect(
      validateAdministrationSignal({
        name: "projection_load",
        portal: "security",
        lane: "security",
        outcome: "ok",
        reason: "current",
        durationBucket: "lt500",
      }),
    ).toBe(true);
    expect(
      validateAdministrationSignal({
        name: "projection_load",
        portal: "security",
        lane: "security",
        outcome: "ok",
        reason: "raw provider 10.0.0.1" as never,
        durationBucket: "lt500",
      }),
    ).toBe(false);
  });
});
