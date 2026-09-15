import { describe, expect, it } from "vitest";
import {
  isSecurityInvalidationEvent,
  laneAllowsPayload,
  safeSecurityProblem,
  securityQueryKey,
  signalLanes,
} from "../packages/security-contracts/src";
describe("P5.6 security contracts", () => {
  it("keeps five signal lanes separate", () => {
    expect(signalLanes).toHaveLength(5);
    expect(laneAllowsPayload("security", "denial")).toBe(true);
    expect(laneAllowsPayload("security", "audit_reference")).toBe(false);
  });
  it("validates events and query scope", () => {
    expect(
      isSecurityInvalidationEvent({
        eventType: "hcam.security.projection.changed.v1",
        version: "1.0.0",
        departmentRef: "SYN-DEPT-01",
        sequence: 4,
        lane: "security",
        queryScopes: ["security.denials"],
        generated: true,
      }),
    ).toBe(true);
    expect(
      securityQueryKey({
        departmentRef: "SYN-DEPT-01",
        lane: "audit",
        state: "current",
        cursor: null,
        limit: 10,
      })[1],
    ).toBe("security");
    expect(safeSecurityProblem("raw failure")).toBe("safe_failure");
  });
});
