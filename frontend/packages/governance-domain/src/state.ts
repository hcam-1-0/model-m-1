export type GovernanceViewState =
  | "loading"
  | "empty"
  | "ready"
  | "partial"
  | "stale"
  | "degraded"
  | "denied"
  | "conflict"
  | "failure"
  | "recovery"
  | "unknown";
export function governanceState(input: {
  readonly authorized: boolean;
  readonly loading: boolean;
  readonly count: number;
  readonly stale: boolean;
  readonly complete: boolean;
  readonly failed: boolean;
}): GovernanceViewState {
  if (!input.authorized) return "denied";
  if (input.loading) return "loading";
  if (input.failed) return "failure";
  if (input.count === 0) return "empty";
  if (input.stale) return "stale";
  if (!input.complete) return "partial";
  return "ready";
}
