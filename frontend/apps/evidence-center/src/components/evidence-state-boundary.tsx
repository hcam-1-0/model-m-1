import { AlertTriangle, CheckCircle2, CircleDashed, ShieldAlert } from "lucide-react";
import type { UiState } from "@hcam/contracts";

const icons = {
  ready: CheckCircle2,
  partial: AlertTriangle,
  stale: CircleDashed,
  degraded: ShieldAlert,
} as const;
export function EvidenceStateBoundary({
  state,
  detail,
}: {
  readonly state: Extract<UiState, "ready" | "partial" | "stale" | "degraded">;
  readonly detail: string;
}) {
  const Icon = icons[state];
  return (
    <section className={`state-boundary state-${state}`} role="status">
      <Icon size={18} />
      <div>
        <strong>{state.replaceAll("_", " ")}</strong>
        <p>{detail}</p>
      </div>
    </section>
  );
}
