import { describe, expect, it } from "vitest";
import { resolveInvestigationEvidenceAuthority } from "../packages/capabilities/src";
import { validateOpaqueSource } from "../packages/evidence-domain/src";
import {
  findProhibitedGeneratedFields,
  generatedEvidenceReferences,
  generatedInvestigationQueue,
  generatedProvenance,
} from "../packages/investigation-fixtures/src";
const forbiddenText =
  /password|secret_ref|credential|camera_locator|source_locator|signed_url|biometric_template|vehicle_plate|person_name|(?:rtsp|whep|webrtc|file):\/\//iu;
describe("P5.5 security", () => {
  it("excludes sensitive, locator, media, and identity fields", () => {
    const fixture = {
      investigations: generatedInvestigationQueue(50),
      evidence: generatedEvidenceReferences(40),
      provenance: generatedProvenance(50),
    };
    expect(findProhibitedGeneratedFields(fixture)).toEqual([]);
    expect(JSON.stringify(fixture)).not.toMatch(forbiddenText);
  });
  it("rejects enabled source operations and keeps hostile text inert", () => {
    const source = generatedEvidenceReferences(1)[0]!.source;
    expect(validateOpaqueSource(source)).toEqual([]);
    expect(validateOpaqueSource({ ...source, resolved: true as never })).toContain(
      "source_operation_enabled",
    );
    for (const value of [
      "<script>alert(1)</script>",
      "javascript:alert(1)",
      "../../secret",
      "identity confirmed",
    ]) {
      const node = document.createElement("span");
      node.textContent = value;
      expect(node.querySelector("script")).toBeNull();
      expect(node.textContent).toBe(value);
    }
  });
  it("fails closed for scope, purpose, freshness, and capability mismatches", () => {
    const baseline = {
      departmentMatches: true,
      purposeMatches: true,
      policyCurrent: true,
      capability: "investigations.viewer" as const,
      capabilities: ["investigations.viewer" as const],
    };
    expect(resolveInvestigationEvidenceAuthority(baseline)).toEqual({
      allowed: true,
      reason: "allowed",
    });
    expect(
      resolveInvestigationEvidenceAuthority({ ...baseline, departmentMatches: false }),
    ).toMatchObject({ allowed: false, reason: "department_mismatch" });
    expect(
      resolveInvestigationEvidenceAuthority({ ...baseline, purposeMatches: false }),
    ).toMatchObject({ allowed: false, reason: "department_mismatch" });
    expect(
      resolveInvestigationEvidenceAuthority({ ...baseline, policyCurrent: false }),
    ).toMatchObject({ allowed: false, reason: "session_stale" });
    expect(resolveInvestigationEvidenceAuthority({ ...baseline, capabilities: [] })).toMatchObject({
      allowed: false,
      reason: "capability_missing",
    });
    expect(
      resolveInvestigationEvidenceAuthority({
        ...baseline,
        capabilities: ["administrator"],
      }),
    ).toMatchObject({ allowed: true, reason: "allowed" });
  });
});
