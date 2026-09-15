import { describe, expect, it } from "vitest";
import {
  evidenceProfileLimits,
  evidenceProfiles,
  limitsForEvidenceProfile,
} from "../packages/evidence-domain/src";
import {
  investigationProfileLimits,
  investigationProfiles,
  limitsForInvestigationProfile,
} from "../packages/investigation-domain/src";
describe("P5.5 resource profiles", () => {
  it("scale bounded presentation without changing authority", () => {
    expect(investigationProfiles).toHaveLength(5);
    expect(evidenceProfiles).toHaveLength(5);
    for (const profile of investigationProfiles) {
      expect(investigationProfileLimits[profile].authorityChanged).toBe(false);
      expect(investigationProfileLimits[profile].semanticsChanged).toBe(false);
      expect(limitsForInvestigationProfile(profile)).toBe(investigationProfileLimits[profile]);
    }
    for (const profile of evidenceProfiles) {
      expect(evidenceProfileLimits[profile].authorityChanged).toBe(false);
      expect(evidenceProfileLimits[profile].sourceAccessChanged).toBe(false);
      expect(limitsForEvidenceProfile(profile)).toBe(evidenceProfileLimits[profile]);
    }
    expect(investigationProfileLimits.future_server.timelinePageSize).toBeGreaterThan(
      investigationProfileLimits.low_resource.timelinePageSize,
    );
  });
});
