import type {
  EvidenceReference,
  EvidenceVerificationEvent,
} from "../../investigation-contracts/src";

export interface IntegrityPresentation {
  readonly label: string;
  readonly caution: string;
  readonly establishesTruth: false;
  readonly establishesAuthenticity: false;
  readonly establishesAdmissibility: false;
}
export function integrityPresentation(reference: EvidenceReference): IntegrityPresentation {
  const labels = {
    not_checked: "Not checked",
    digest_observed: "Digest observed",
    digest_mismatch: "Digest mismatch",
    unknown: "Unknown",
  } as const;
  return {
    label: labels[reference.integrity],
    caution: "Integrity state describes a generated reference check only.",
    establishesTruth: false,
    establishesAuthenticity: false,
    establishesAdmissibility: false,
  };
}
export function orderVerificationHistory(events: readonly EvidenceVerificationEvent[]) {
  return [...events].sort((left, right) => left.sequence - right.sequence).slice(0, 100);
}
