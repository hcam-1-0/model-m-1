import { describe, expect, it } from "vitest";
import { governanceProfiles, governanceProfile } from "../packages/governance-domain/src";
import {
  operationsProfiles,
  operationsProfilePresentation,
} from "../packages/platform-operations-domain/src";
describe("P5.6 dynamic profiles", () => {
  it("preserves authority and truth across all six profiles", () => {
    expect(governanceProfiles).toHaveLength(6);
    for (const profile of governanceProfiles)
      expect(governanceProfile(profile)).toMatchObject({
        authorityInvariant: true,
        scopeInvariant: true,
        actionEligibilityInvariant: true,
      });
    expect(operationsProfiles).toHaveLength(6);
    for (const profile of operationsProfiles)
      expect(operationsProfilePresentation(profile)).toMatchObject({
        authorityInvariant: true,
        truthInvariant: true,
        accessibilityInvariant: true,
      });
  });
});
