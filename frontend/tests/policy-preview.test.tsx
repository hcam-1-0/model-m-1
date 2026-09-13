import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { EvidencePolicyPreviewPage } from "../apps/evidence-center/src/pages/evidence-policy-preview-page";
import { forbiddenPolicyActions, validatePolicyPreview } from "../packages/evidence-domain/src";
import { generatedPolicyPreview } from "../packages/investigation-fixtures/src";
afterEach(cleanup);
describe("P5.5 policy previews", () => {
  it("remain generated and non-operative", () => {
    for (let index = 1; index <= 5; index += 1)
      expect(validatePolicyPreview(generatedPolicyPreview(index))).toEqual([]);
    render(<EvidencePolicyPreviewPage />);
    expect(screen.getAllByText("Disabled")).toHaveLength(5);
    for (const action of forbiddenPolicyActions)
      expect(screen.queryByRole("button", { name: new RegExp(action, "i") })).toBeNull();
  });
  it("rejects executable, invalid, unbounded, and unexplained partial previews", () => {
    const preview = generatedPolicyPreview(1);
    const hostile = {
      ...preview,
      executable: true,
      policyReference: "REAL-POLICY",
      targets: Array.from({ length: 101 }, () => preview.targets[0]!),
      completeness: "unknown",
      limitations: [],
    } as unknown as typeof preview;
    expect(validatePolicyPreview(hostile)).toEqual([
      "preview_is_executable",
      "invalid_policy_reference",
      "target_ceiling_exceeded",
      "missing_limitation",
    ]);
  });
});
