import type { ReactNode } from "react";
import type { UiState } from "@hcam/contracts";
import { StateBanner } from "@hcam/ui";
export function InvestigationStateBoundary({
  state,
  children,
}: {
  readonly state: UiState;
  readonly children: ReactNode;
}) {
  if (["ready", "partial", "correction", "retracted"].includes(state))
    return (
      <>
        {state !== "ready" ? (
          <StateBanner
            state={state}
            title={
              state === "correction"
                ? "Correction impact is incomplete"
                : state === "retracted"
                  ? "Retraction is visible in append-only history"
                  : "Generated projection is incomplete"
            }
            detail="Authority, omissions, and required refresh remain visible."
          />
        ) : null}
        {children}
      </>
    );
  return (
    <StateBanner
      state={state}
      title={`Investigation view is ${state}`}
      detail="No hidden source, cached truth, or operational fallback is used."
    />
  );
}
