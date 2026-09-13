import { AlertTriangle, Inbox, LoaderCircle, ShieldX } from "lucide-react";
import type { ReactNode } from "react";
import type { LiveUiState } from "@hcam/camera-live-domain";

export function StateBoundary({
  state,
  children,
}: {
  readonly state: LiveUiState;
  readonly children: ReactNode;
}) {
  if (state === "ready" || state === "partial")
    return (
      <>
        {state === "partial" ? (
          <div className="state-banner">
            <AlertTriangle size={16} />
            <span>Some generated sources are incomplete or unavailable.</span>
          </div>
        ) : null}
        {children}
      </>
    );
  const Icon =
    state === "loading"
      ? LoaderCircle
      : state === "empty"
        ? Inbox
        : state === "denied"
          ? ShieldX
          : AlertTriangle;
  return (
    <div className="state-boundary" role="status">
      <Icon size={24} />
      <strong>{state}</strong>
      <p>The authoritative generated projection cannot be shown in its normal form.</p>
    </div>
  );
}
