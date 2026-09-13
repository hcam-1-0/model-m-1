import { describe, expect, it } from "vitest";
import {
  resourceProfiles,
  viewportProfiles,
  type ResourceProfileId,
} from "../packages/quality-contracts/src";
import {
  classifyBrowserAvailability,
  profileAuthorityInvariant,
} from "../packages/quality-domain/src";

describe("P5.7 browser and resource profiles", () => {
  it("never turns a missing browser into a passing result", () => {
    expect(classifyBrowserAvailability(true, false)).toBe("pass");
    expect(classifyBrowserAvailability(false, true)).toBe("blocked");
    expect(classifyBrowserAvailability(false, false)).toBe("unsupported");
  });

  it("preserves authority across all six profiles and seven viewports", () => {
    const authorities = Object.fromEntries(
      resourceProfiles.map(({ id }) => [id, "camera.viewer"]),
    ) as Record<ResourceProfileId, string>;
    expect(
      profileAuthorityInvariant(
        resourceProfiles.map(({ id }) => id),
        authorities,
      ),
    ).toBe(true);
    expect(profileAuthorityInvariant([], authorities)).toBe(false);
    expect(viewportProfiles).toHaveLength(7);
  });
});
