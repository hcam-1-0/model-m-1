import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { EvidenceStateMatrix } from "../apps/evidence-center/src/components/evidence-state-matrix";
import {
  evidenceStateAxes,
  evidenceStateMatrix,
  hasSingleVerificationConclusion,
  integrityPresentation,
  orderVerificationHistory,
} from "../packages/evidence-domain/src";
import {
  generatedEvidenceReferences,
  generatedVerificationHistory,
} from "../packages/investigation-fixtures/src";
afterEach(cleanup);
describe("P5.5 evidence state matrix", () => {
  it("renders seven independent axes without a combined conclusion", () => {
    const reference = generatedEvidenceReferences(1)[0]!;
    expect(evidenceStateAxes).toHaveLength(7);
    expect(hasSingleVerificationConclusion(reference)).toBe(false);
    render(<EvidenceStateMatrix reference={reference} />);
    for (const axis of evidenceStateAxes)
      expect(screen.getByText(axis.replaceAll("_", " "))).toBeVisible();
    expect(screen.getByText("No combined verification conclusion")).toBeVisible();
  });
  it("presents every integrity state without collapsing evidence axes", () => {
    const reference = generatedEvidenceReferences(4)[0]!;
    expect(evidenceStateMatrix(reference)).toHaveLength(7);
    for (const integrity of [
      "not_checked",
      "digest_observed",
      "digest_mismatch",
      "unknown",
    ] as const)
      expect(integrityPresentation({ ...reference, integrity })).toMatchObject({
        establishesTruth: false,
        establishesAuthenticity: false,
        establishesAdmissibility: false,
      });
    const history = generatedVerificationHistory();
    expect(orderVerificationHistory([...history].reverse())[0]?.sequence).toBe(1);
    expect(orderVerificationHistory(Array.from({ length: 101 }, () => history[0]!))).toHaveLength(
      100,
    );
    expect(
      hasSingleVerificationConclusion({
        ...reference,
        singleVerificationConclusion: true,
      } as unknown as typeof reference),
    ).toBe(true);
  });
});
