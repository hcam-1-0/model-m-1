import { describe, expect, it } from "vitest";
import {
  authorize,
  canTransitionChange,
  governanceState,
  isOpaqueSecretReference,
  retentionPreview,
} from "../packages/governance-domain/src";
const target = {
  departmentRef: "SYN-DEPT-01",
  purposeCode: "SYN-PURPOSE",
  requiredCapability: "admin.viewer",
  policyRevision: "R7",
};
describe("P5.6 governance domain", () => {
  it("defaults to deny and matches the RLS projection", () => {
    expect(
      authorize(
        {
          actorRef: null,
          sessionCurrent: true,
          departmentRef: "SYN-DEPT-01",
          purposeCode: "SYN-PURPOSE",
          capabilities: ["admin.viewer"],
          policyRevision: "R7",
        },
        target,
      ).allowed,
    ).toBe(false);
    expect(
      authorize(
        {
          actorRef: "SYN-ACTOR-01",
          sessionCurrent: true,
          departmentRef: "SYN-DEPT-01",
          purposeCode: "SYN-PURPOSE",
          capabilities: ["admin.viewer"],
          policyRevision: "R7",
        },
        target,
      ).allowed,
    ).toBe(true);
  });
  it("allows only typed lifecycle edges", () => {
    expect(canTransitionChange("draft", "submitted")).toBe(true);
    expect(canTransitionChange("draft", "approved_non_effective")).toBe(false);
  });
  it("keeps secrets opaque and policies non-operative", () => {
    expect(isOpaqueSecretReference("SYN-SECRET-REF-PROVIDER-01")).toBe(true);
    expect(isOpaqueSecretReference("plain-password")).toBe(false);
    expect(retentionPreview().executable).toBe(false);
  });
  it("selects explicit UI states", () => {
    expect(
      governanceState({
        authorized: false,
        loading: false,
        count: 1,
        stale: false,
        complete: true,
        failed: false,
      }),
    ).toBe("denied");
    expect(
      governanceState({
        authorized: true,
        loading: false,
        count: 1,
        stale: false,
        complete: true,
        failed: false,
      }),
    ).toBe("ready");
  });
});
