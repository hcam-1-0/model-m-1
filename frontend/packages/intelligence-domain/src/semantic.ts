import {
  analyticalConceptKinds,
  type AnalyticalConceptKind,
  type AuthorityClass,
} from "../../intelligence-contracts/src";

export const conceptPresentation: Readonly<
  Record<AnalyticalConceptKind, { label: string; authority: AuthorityClass; caution: string }>
> = Object.freeze({
  observation: {
    label: "Source observation",
    authority: "source_fact",
    caution: "What a generated source reported",
  },
  inference: {
    label: "Analytical inference",
    authority: "analytical_only",
    caution: "Derived, not directly observed",
  },
  hypothesis: {
    label: "Working hypothesis",
    authority: "analytical_only",
    caution: "Unconfirmed analytical proposition",
  },
  candidate: {
    label: "Candidate comparison",
    authority: "analytical_only",
    caution: "Identity is not established",
  },
  proposed_alert: {
    label: "Proposed alert",
    authority: "analytical_only",
    caution: "Requires mandatory human review",
  },
  review: {
    label: "Human review record",
    authority: "human_decision",
    caution: "Decision for the generated record only",
  },
  correction: {
    label: "Correction",
    authority: "historical_record",
    caution: "Append-only correction to prior projection",
  },
  lifecycle: {
    label: "Lifecycle record",
    authority: "historical_record",
    caution: "Chronological system state",
  },
});
const forbiddenClaims =
  /\b(identity confirmed|guilty|criminal|suspect identified|operational truth)\b/iu;
export function presentationFor(kind: AnalyticalConceptKind) {
  return conceptPresentation[kind];
}
export function isAnalyticalConceptKind(value: unknown): value is AnalyticalConceptKind {
  return analyticalConceptKinds.includes(value as AnalyticalConceptKind);
}
export function assertSafeAnalyticalCopy(value: string): string {
  if (!value || value.length > 240 || forbiddenClaims.test(value))
    throw new Error("forbidden_analytical_claim");
  return value;
}
