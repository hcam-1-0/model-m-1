import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CandidateMatrix } from "../apps/intelligence-center/src/components/candidate-matrix";
import { ContradictionPanel } from "../apps/intelligence-center/src/components/contradiction-panel";
import { generatedCandidate } from "../packages/intelligence-fixtures/src";
afterEach(cleanup);
describe("P5.4 candidate uncertainty", () => {
  it("shows support, contradiction, ambiguity, missingness and abstention", () => {
    const value = generatedCandidate();
    render(
      <>
        <CandidateMatrix candidate={value} />
        <ContradictionPanel candidate={value} />
      </>,
    );
    for (const role of ["supports", "contradicts", "ambiguous", "missing"])
      expect(screen.getAllByText(role).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Identity not established/i)).not.toHaveLength(0);
    expect(screen.getByText(/Comparison abstained/)).toBeVisible();
  });
});
