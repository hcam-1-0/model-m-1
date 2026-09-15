import {
  generatedCaseAllocation,
  journeyDefinitions,
  localeTimeProfiles,
  mandatoryStates,
  resourceProfiles,
  viewportProfiles,
  type GeneratedQualityCase,
  type QualityEvidenceNode,
} from "../../quality-contracts/src/index";
import {
  buildTerminalProjection,
  deterministicDigest,
  findProhibitedFields,
  validateEvidenceGraph,
  validatePortfolio,
} from "../../quality-domain/src/index";

export interface HarnessSummary {
  readonly status: "pass" | "fail";
  readonly generatedOnly: true;
  readonly caseCount: number;
  readonly findings: readonly string[];
  readonly terminalDigest: string;
  readonly coverage: {
    readonly categories: number;
    readonly journeys: number;
    readonly states: number;
    readonly viewports: number;
    readonly localeTimeProfiles: number;
    readonly resourceProfiles: number;
  };
}

export function buildQualityEvidenceGraph(
  cases: readonly GeneratedQualityCase[],
): readonly QualityEvidenceNode[] {
  const requirements: QualityEvidenceNode[] = [
    { id: "REQ-GENERATED", kind: "requirement", dependsOn: [] },
    { id: "REQ-AUTHORITY", kind: "requirement", dependsOn: [] },
    { id: "REQ-REPLAY", kind: "requirement", dependsOn: [] },
  ];
  const caseNodes: QualityEvidenceNode[] = cases.slice(0, 32).map((item) => ({
    id: `CASE-${item.ref}`,
    kind: "case",
    dependsOn: ["REQ-GENERATED", "REQ-AUTHORITY"],
  }));
  const resultNodes: QualityEvidenceNode[] = caseNodes.map((item, index) => ({
    id: `RESULT-${String(index + 1).padStart(2, "0")}`,
    kind: "result",
    dependsOn: [item.id],
  }));
  return [
    ...requirements,
    ...caseNodes,
    ...resultNodes,
    {
      id: "CLAIM-LOCAL-GENERATED-QUALITY",
      kind: "claim",
      dependsOn: resultNodes.map(({ id }) => id),
    },
    {
      id: "LIMIT-NOT-PRODUCTION",
      kind: "limitation",
      dependsOn: ["CLAIM-LOCAL-GENERATED-QUALITY"],
    },
  ];
}

export function runQualityHarness(cases: readonly GeneratedQualityCase[]): HarnessSummary {
  const findings = [
    ...validatePortfolio(cases),
    ...findProhibitedFields(cases).map((path) => `prohibited:${path}`),
  ];
  const graph = buildQualityEvidenceGraph(cases);
  findings.push(...validateEvidenceGraph(graph).map((finding) => `evidence:${finding}`));
  const terminal = buildTerminalProjection(cases);
  return {
    status: findings.length === 0 ? "pass" : "fail",
    generatedOnly: true,
    caseCount: cases.length,
    findings,
    terminalDigest: deterministicDigest(terminal),
    coverage: {
      categories: Object.keys(generatedCaseAllocation).length,
      journeys: journeyDefinitions.length,
      states: mandatoryStates.length,
      viewports: viewportProfiles.length,
      localeTimeProfiles: localeTimeProfiles.length,
      resourceProfiles: resourceProfiles.length,
    },
  };
}

export function verifyCleanReplay(cases: readonly GeneratedQualityCase[]): boolean {
  const first = runQualityHarness(cases);
  const second = runQualityHarness(cases.map((item) => ({ ...item })));
  return (
    first.status === "pass" &&
    second.status === "pass" &&
    first.terminalDigest === second.terminalDigest
  );
}
