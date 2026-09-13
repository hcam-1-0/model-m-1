import type { ReactNode } from "react";
import { StateBanner } from "@hcam/ui";
import type { UiState } from "@hcam/contracts";

export function StateBoundary({
  state,
  children,
}: {
  readonly state: UiState;
  readonly children: ReactNode;
}) {
  if (state === "ready") return children;
  return (
    <>
      <StateBanner
        state={state}
        title={`Situation state: ${state}`}
        detail="This status is carried from an authoritative generated projection; no client conclusion was created."
      />
      {children}
    </>
  );
}
