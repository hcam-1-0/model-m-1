import { describe, expect, it } from "vitest";
import { resolveGovernanceAuthority } from "@hcam/capabilities";
describe("P5.6 access and RLS boundary", () => {
  it("denies every missing scope dimension", () => {
    const base = {
      sessionCurrent: true,
      departmentMatches: true,
      purposeMatches: true,
      policyCurrent: true,
      requiredCapability: "security.viewer" as const,
      capabilities: ["security.viewer" as const],
    };
    expect(resolveGovernanceAuthority(base).allowed).toBe(true);
    expect(resolveGovernanceAuthority({ ...base, departmentMatches: false }).allowed).toBe(false);
    expect(resolveGovernanceAuthority({ ...base, purposeMatches: false }).allowed).toBe(false);
    expect(resolveGovernanceAuthority({ ...base, policyCurrent: false }).allowed).toBe(false);
    expect(resolveGovernanceAuthority({ ...base, capabilities: [] }).allowed).toBe(false);
  });
});
