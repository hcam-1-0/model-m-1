import { describe, expect, it } from "vitest";
import {
  generatedCaseAllocation,
  journeyDefinitions,
  localeTimeProfiles,
  mandatoryStates,
  qualityContractVersion,
  qualitySurfaces,
  resourceProfiles,
  terminalReasonCodes,
  viewportProfiles,
} from "../packages/quality-contracts/src";

describe("P5.7 frozen quality contracts", () => {
  it("preserves every selected portfolio count", () => {
    expect(qualityContractVersion).toBe("1.0.0");
    expect(qualitySurfaces).toHaveLength(9);
    expect(journeyDefinitions).toHaveLength(14);
    expect(mandatoryStates).toHaveLength(20);
    expect(viewportProfiles).toHaveLength(7);
    expect(localeTimeProfiles).toHaveLength(5);
    expect(resourceProfiles).toHaveLength(6);
    expect(Object.values(generatedCaseAllocation).reduce((total, count) => total + count, 0)).toBe(
      2048,
    );
    expect(terminalReasonCodes).toContain("unresolved_blocker");
  });
});
