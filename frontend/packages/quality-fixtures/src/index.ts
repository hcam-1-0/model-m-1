import {
  generatedCaseAllocation,
  journeyDefinitions,
  localeTimeProfiles,
  mandatoryStates,
  qualitySurfaces,
  resourceProfiles,
  viewportProfiles,
  workloadProfiles,
  type ExpectedOutcome,
  type GeneratedCaseCategory,
  type GeneratedQualityCase,
} from "../../quality-contracts/src/index";

const categories = Object.entries(generatedCaseAllocation) as readonly [
  GeneratedCaseCategory,
  number,
][];

function outcomeFor(state: (typeof mandatoryStates)[number]): ExpectedOutcome {
  if (state === "denied" || state === "scope_changed" || state === "session_expired") return "deny";
  if (state === "event_gap" || state === "recovery") return "recover_by_authoritative_refetch";
  if (state === "abstention") return "abstain";
  if (state === "non_effective" || state === "pending_review") return "remain_non_effective";
  if (["partial", "stale", "degraded", "failure", "offline", "unsupported"].includes(state))
    return "degrade";
  return "allow_generated_read";
}

function authorityFor(expected: ExpectedOutcome): GeneratedQualityCase["authority"] {
  if (expected === "remain_non_effective") return "non_effective";
  if (expected === "abstain") return "mandatory_review";
  return "read_only";
}

function truthFor(sequence: number): GeneratedQualityCase["truth"] {
  return ["observation", "inference", "hypothesis", "proposal", "qualified_system_state"][
    sequence % 5
  ] as GeneratedQualityCase["truth"];
}

export function generateQualityCases(): readonly GeneratedQualityCase[] {
  const output: GeneratedQualityCase[] = [];
  for (const [category, count] of categories)
    for (let local = 0; local < count; local += 1) {
      const sequence = output.length + 1;
      const state = mandatoryStates[(sequence - 1) % mandatoryStates.length] ?? "failure";
      const expected = outcomeFor(state);
      output.push({
        ref: `SYN-P57-CASE-${String(sequence).padStart(4, "0")}`,
        generatedOnly: true,
        category,
        sequence,
        seed: 570000 + sequence * 17,
        journeyId: journeyDefinitions[(sequence - 1) % journeyDefinitions.length]?.id ?? "J14",
        state,
        surface: qualitySurfaces[(sequence - 1) % qualitySurfaces.length] ?? "command",
        viewportId: viewportProfiles[(sequence - 1) % viewportProfiles.length]?.id ?? "V03",
        localeTimeId: localeTimeProfiles[(sequence - 1) % localeTimeProfiles.length]?.id ?? "L01",
        resourceProfileId: resourceProfiles[(sequence - 1) % resourceProfiles.length]?.id ?? "R01",
        workload: workloadProfiles[(sequence - 1) % workloadProfiles.length] ?? "C1",
        expected,
        authority: authorityFor(expected),
        truth: truthFor(sequence),
      });
    }
  return output;
}

export const p57GeneratedCases = Object.freeze(generateQualityCases());

export const p57FaultScenarios = Object.freeze([
  { id: "F01", event: "gap", expected: "refetch_required" },
  { id: "F02", event: "retry", expected: "recovering" },
  { id: "F03", event: "authoritative_success", expected: "recovered" },
  { id: "F04", event: "authoritative_failure", expected: "terminal_failure" },
  { id: "F05", event: "reset", expected: "healthy" },
]);

export const hostileUnicodeFixtures = Object.freeze([
  "ગુજરાત પોલીસ",
  "हिंदी नियंत्रण कक्ष",
  "A\u0301\u200D\u2066B\u2069",
  "مرحبا\u202Eabc",
  "［ＰＳＥＵＤＯ］ long-long-long-label-without-a-break",
]);

export const generatedQualityManifest = Object.freeze({
  schemaVersion: "hcam.phase5.p5_7.generated_manifest.v1",
  generatedOnly: true,
  exactCaseCount: 2048,
  categoryAllocation: generatedCaseAllocation,
  journeyCount: journeyDefinitions.length,
  mandatoryStateCount: mandatoryStates.length,
  viewportCount: viewportProfiles.length,
  localeTimeProfileCount: localeTimeProfiles.length,
  resourceProfileCount: resourceProfiles.length,
  workloads: workloadProfiles,
  seedRule: "570000_plus_sequence_times_17",
});
