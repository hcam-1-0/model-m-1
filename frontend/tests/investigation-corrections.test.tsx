import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CorrectionRetractionPanel } from "../apps/investigation-center/src/components/correction-retraction-panel";
import { ImpactClosureTable } from "../apps/investigation-center/src/components/impact-closure-table";
import {
  correctionLineage,
  summarizeImpactClosure,
  validateAppendOnlyCorrection,
} from "../packages/investigation-domain/src";
import { generatedCorrection } from "../packages/investigation-fixtures/src";
afterEach(cleanup);
describe("P5.5 corrections and retractions", () => {
  it("retains predecessor and exposes incomplete impact closure", () => {
    const correction = generatedCorrection(1);
    expect(validateAppendOnlyCorrection(correction)).toEqual([]);
    expect(summarizeImpactClosure(correction.impactTargets).complete).toBe(false);
    render(
      <>
        <CorrectionRetractionPanel record={correction} />
        <ImpactClosureTable
          targets={correction.impactTargets}
          summary={summarizeImpactClosure(correction.impactTargets)}
        />
      </>,
    );
    expect(screen.getByText("Predecessor retained")).toBeVisible();
    expect(screen.getByText("History rewritten")).toBeVisible();
    expect(screen.getByRole("table")).toBeVisible();
  });
  it("rejects cycles, rewrites, invalid reasons, and unbounded impacts", () => {
    const correction = generatedCorrection(2);
    const hostile = {
      ...correction,
      successorRef: correction.predecessorRef,
      reasonCode: "x".repeat(65),
      impactTargets: [],
      rewritesHistory: true,
    } as unknown as typeof correction;
    expect(validateAppendOnlyCorrection(hostile)).toEqual([
      "lineage_cycle",
      "history_rewrite_forbidden",
      "invalid_reason_code",
      "invalid_impact_target_count",
    ]);
    expect(validateAppendOnlyCorrection({ ...correction, reasonCode: "" })).toContain(
      "invalid_reason_code",
    );
    expect(
      validateAppendOnlyCorrection({
        ...correction,
        impactTargets: Array.from({ length: 101 }, () => correction.impactTargets[0]!),
      }),
    ).toContain("invalid_impact_target_count");
    expect(correctionLineage([correction])).toEqual([
      {
        predecessorRef: correction.predecessorRef,
        successorRef: correction.successorRef,
        kind: correction.kind,
        retained: true,
      },
    ]);
  });
});
