import { describe, expect, it } from "vitest";
import { validateEvidenceGraph } from "../packages/quality-domain/src";
import { p57GeneratedCases } from "../packages/quality-fixtures/src";
import { buildQualityEvidenceGraph } from "../packages/quality-harness/src";

describe("P5.7 evidence graph", () => {
  it("is acyclic and all dependencies resolve", () => {
    const graph = buildQualityEvidenceGraph(p57GeneratedCases);
    expect(validateEvidenceGraph(graph)).toEqual([]);
  });

  it("reports duplicate, missing, and cyclic nodes", () => {
    const invalid = [
      { id: "A", kind: "case", dependsOn: ["B", "MISSING"] },
      { id: "B", kind: "result", dependsOn: ["A"] },
      { id: "C", kind: "result", dependsOn: [] },
      { id: "C", kind: "result", dependsOn: [] },
    ] as const;
    expect(validateEvidenceGraph(invalid)).toEqual([
      "cycle:A",
      "duplicate_node",
      "missing_dependency:A:MISSING",
    ]);
  });
});
