import {
  generatedCaseAllocation,
  journeyDefinitions,
  localeTimeProfiles,
  mandatoryStates,
  prohibitedEvidenceKeys,
  qualitySurfaces,
  resourceProfiles,
  viewportProfiles,
  workloadProfiles,
  type GeneratedQualityCase,
  type HardBudget,
  type QualityEvidenceNode,
  type QualityResult,
  type ResourceProfileId,
} from "../../quality-contracts/src/index";

export function canonicalize(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(",")}]`;
  const entries = Object.entries(value as Readonly<Record<string, unknown>>).sort(([a], [b]) =>
    a.localeCompare(b, "en"),
  );
  return `{${entries.map(([key, item]) => `${JSON.stringify(key)}:${canonicalize(item)}`).join(",")}}`;
}

export function deterministicDigest(value: unknown): string {
  let hash = 0xcbf29ce484222325n;
  for (const byte of new TextEncoder().encode(canonicalize(value))) {
    hash ^= BigInt(byte);
    hash = BigInt.asUintN(64, hash * 0x100000001b3n);
  }
  return hash.toString(16).toUpperCase().padStart(16, "0");
}

type GeneratedQualityCaseCandidate = Omit<GeneratedQualityCase, "generatedOnly" | "ref"> & {
  readonly generatedOnly: boolean;
  readonly ref: string;
};

export function validateGeneratedCase(item: GeneratedQualityCaseCandidate): QualityResult {
  if (!item.generatedOnly || !item.ref.startsWith("SYN-P57-CASE-"))
    return { ref: item.ref, status: "fail", reason: "generated_boundary_breached" };
  if (!journeyDefinitions.some(({ id }) => id === item.journeyId))
    return { ref: item.ref, status: "fail", reason: "contract_invalid" };
  if (!mandatoryStates.includes(item.state) || !qualitySurfaces.includes(item.surface))
    return { ref: item.ref, status: "fail", reason: "contract_invalid" };
  if (!viewportProfiles.some(({ id }) => id === item.viewportId))
    return { ref: item.ref, status: "fail", reason: "contract_invalid" };
  if (!localeTimeProfiles.some(({ id }) => id === item.localeTimeId))
    return { ref: item.ref, status: "fail", reason: "contract_invalid" };
  if (!resourceProfiles.some(({ id }) => id === item.resourceProfileId))
    return { ref: item.ref, status: "fail", reason: "contract_invalid" };
  if (!workloadProfiles.includes(item.workload))
    return { ref: item.ref, status: "fail", reason: "contract_invalid" };
  if (item.authority === "mandatory_review" && item.expected === "allow_generated_read")
    return { ref: item.ref, status: "fail", reason: "authority_changed" };
  return { ref: item.ref, status: "pass", reason: "quality_pass" };
}

export function validatePortfolio(cases: readonly GeneratedQualityCase[]): readonly string[] {
  const findings: string[] = [];
  if (cases.length !== 2048) findings.push("case_count");
  if (new Set(cases.map(({ ref }) => ref)).size !== cases.length) findings.push("case_identity");
  for (const [category, expected] of Object.entries(generatedCaseAllocation)) {
    const actual = cases.filter((item) => item.category === category).length;
    if (actual !== expected) findings.push(`category:${category}`);
  }
  for (const { id } of journeyDefinitions)
    if (!cases.some((item) => item.journeyId === id)) findings.push(`journey:${id}`);
  for (const state of mandatoryStates)
    if (!cases.some((item) => item.state === state)) findings.push(`state:${state}`);
  for (const result of cases.map(validateGeneratedCase))
    if (result.status !== "pass") findings.push(`${result.ref}:${result.reason}`);
  return findings;
}

export function evaluateHardBudget(actual: number, budget: HardBudget): QualityResult {
  if (!Number.isFinite(actual) || actual < 0)
    return { ref: budget.metric, status: "fail", reason: "contract_invalid" };
  return actual <= budget.maximum
    ? { ref: budget.metric, status: "pass", reason: "quality_pass" }
    : { ref: budget.metric, status: "fail", reason: "hard_budget_exceeded" };
}

export function classifyBrowserAvailability(
  primaryAvailable: boolean,
  optionalAvailable: boolean,
): "pass" | "blocked" | "unsupported" {
  if (primaryAvailable) return "pass";
  return optionalAvailable ? "blocked" : "unsupported";
}

export function profileAuthorityInvariant(
  profiles: readonly ResourceProfileId[],
  authorities: Readonly<Record<ResourceProfileId, string>>,
): boolean {
  const values = profiles.map((profile) => authorities[profile]);
  return values.length > 0 && values.every((value) => value === values[0]);
}

export function findProhibitedFields(value: unknown, path = "$"): readonly string[] {
  if (Array.isArray(value))
    return value.flatMap((item, index) => findProhibitedFields(item, `${path}[${index}]`));
  if (value === null || typeof value !== "object") return [];
  return Object.entries(value as Readonly<Record<string, unknown>>).flatMap(([key, item]) => {
    const normalized = key.toLowerCase();
    const own = prohibitedEvidenceKeys.some((blocked) => normalized.includes(blocked))
      ? [`${path}.${key}`]
      : [];
    return [...own, ...findProhibitedFields(item, `${path}.${key}`)];
  });
}

export function validateEvidenceGraph(nodes: readonly QualityEvidenceNode[]): readonly string[] {
  const findings: string[] = [];
  const byId = new Map(nodes.map((node) => [node.id, node]));
  if (byId.size !== nodes.length) findings.push("duplicate_node");
  for (const node of nodes)
    for (const dependency of node.dependsOn)
      if (!byId.has(dependency)) findings.push(`missing_dependency:${node.id}:${dependency}`);
  const visiting = new Set<string>();
  const visited = new Set<string>();
  function visit(id: string): void {
    if (visiting.has(id)) {
      findings.push(`cycle:${id}`);
      return;
    }
    if (visited.has(id)) return;
    visiting.add(id);
    for (const dependency of byId.get(id)?.dependsOn ?? []) visit(dependency);
    visiting.delete(id);
    visited.add(id);
  }
  for (const node of nodes) visit(node.id);
  return [...new Set(findings)].sort();
}

export type RecoveryState =
  "healthy" | "degraded" | "refetch_required" | "recovering" | "recovered" | "terminal_failure";

export function transitionRecovery(
  current: RecoveryState,
  event: "gap" | "retry" | "authoritative_success" | "authoritative_failure" | "reset",
): RecoveryState {
  if (event === "reset") return "healthy";
  if (current === "healthy" && event === "gap") return "refetch_required";
  if (current === "refetch_required" && event === "retry") return "recovering";
  if (current === "recovering" && event === "authoritative_success") return "recovered";
  if (current === "recovering" && event === "authoritative_failure") return "terminal_failure";
  if (current === "degraded" && event === "retry") return "recovering";
  return "degraded";
}

export function buildTerminalProjection(
  cases: readonly GeneratedQualityCase[],
): Readonly<Record<string, unknown>> {
  const results = cases.map(validateGeneratedCase);
  return {
    contractVersion: "1.0.0",
    generatedOnly: true,
    caseCount: cases.length,
    passed: results.filter(({ status }) => status === "pass").length,
    failed: results.filter(({ status }) => status === "fail").length,
    categories: Object.fromEntries(
      Object.keys(generatedCaseAllocation).map((category) => [
        category,
        cases.filter((item) => item.category === category).length,
      ]),
    ),
  };
}
