import type { ProposedAlert } from "../../intelligence-contracts/src";

export type AlertLifecycle = ProposedAlert["lifecycle"];
const transitions: Readonly<Record<AlertLifecycle, readonly AlertLifecycle[]>> = {
  proposed: ["in_review", "retracted", "corrected"],
  in_review: ["confirmed_for_record", "rejected", "retracted", "corrected"],
  confirmed_for_record: ["corrected", "retracted"],
  rejected: ["corrected"],
  retracted: [],
  corrected: ["in_review", "retracted"],
};
export function canTransitionAlert(from: AlertLifecycle, to: AlertLifecycle): boolean {
  return transitions[from].includes(to);
}
export function transitionAlert(alert: ProposedAlert, to: AlertLifecycle): ProposedAlert {
  if (!canTransitionAlert(alert.lifecycle, to)) throw new Error("invalid_lifecycle_transition");
  return {
    ...alert,
    lifecycle: to,
    revision: alert.revision + 1,
    etag: `"SYN-ETAG-${alert.revision + 1}"`,
  };
}
