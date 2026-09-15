import type { ReactNode } from "react";
import type { UiState } from "@hcam/contracts";
import { StateBanner } from "@hcam/ui";
export function IntelligenceStateBoundary({
  state,
  children,
}: {
  readonly state: UiState;
  readonly children: ReactNode;
}) {
  if (state === "ready" || state === "partial" || state === "correction")
    return (
      <>
        {state !== "ready" ? (
          <StateBanner
            state={state}
            title={
              state === "correction"
                ? "Correction requires authoritative refresh"
                : "Some generated producers are incomplete"
            }
            detail="Displayed limits remain visible; mutation is disabled when authority is stale."
          />
        ) : null}
        {children}
      </>
    );
  return (
    <StateBanner
      state={state}
      title={`Intelligence view is ${state}`}
      detail="No operational fallback or hidden data is used."
    />
  );
}
