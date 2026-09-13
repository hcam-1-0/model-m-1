import { describe, expect, it } from "vitest";
import { authorize, projectRlsEquivalent } from "../packages/governance-domain/src";
const contexts = [
  {
    actorRef: "SYN-ACTOR",
    sessionCurrent: true,
    departmentRef: "SYN-DEPT-01",
    purposeCode: "SYN-PURPOSE",
    capabilities: ["admin.viewer"],
    policyRevision: "R7",
  },
  {
    actorRef: "SYN-ACTOR",
    sessionCurrent: true,
    departmentRef: "SYN-DEPT-02",
    purposeCode: "SYN-PURPOSE",
    capabilities: ["admin.viewer"],
    policyRevision: "R7",
  },
  {
    actorRef: "SYN-ACTOR",
    sessionCurrent: false,
    departmentRef: "SYN-DEPT-01",
    purposeCode: "SYN-PURPOSE",
    capabilities: ["admin.viewer"],
    policyRevision: "R7",
  },
] as const;
const target = {
  departmentRef: "SYN-DEPT-01",
  purposeCode: "SYN-PURPOSE",
  requiredCapability: "admin.viewer",
  policyRevision: "R7",
};
describe("P5.6 authorization equivalence", () => {
  it("keeps application and RLS decisions equivalent", () => {
    for (const context of contexts)
      expect(projectRlsEquivalent(context, target)).toEqual(authorize(context, target));
  });
});
