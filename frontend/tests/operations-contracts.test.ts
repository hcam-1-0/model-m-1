import { describe, expect, it } from "vitest";
import {
  isOperationsInvalidationEvent,
  operationsQueryKey,
  safeOperationsProblem,
} from "../packages/operations-contracts/src";
describe("P5.6 operations contracts", () => {
  it("validates bounded invalidations", () => {
    expect(
      isOperationsInvalidationEvent({
        eventType: "hcam.operations.projection.changed.v1",
        version: "1.0.0",
        departmentRef: "SYN-DEPT-01",
        sequence: 1,
        queryScopes: ["operations.services"],
        generated: true,
      }),
    ).toBe(true);
    expect(isOperationsInvalidationEvent({ version: "2.0.0" })).toBe(false);
  });
  it("uses safe keys and problems", () => {
    expect(
      operationsQueryKey({
        departmentRef: "SYN-DEPT-01",
        domain: "platform",
        state: "all",
        cursor: null,
        limit: 50,
      }),
    ).toContain("platform");
    expect(safeOperationsProblem("stack trace")).toBe("safe_failure");
  });
});
