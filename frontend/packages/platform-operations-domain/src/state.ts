export type OperationsViewState =
  | "loading"
  | "empty"
  | "ready"
  | "partial"
  | "stale"
  | "degraded"
  | "denied"
  | "failure"
  | "recovery"
  | "unknown";
export function operationsState(input: {
  readonly authorized: boolean;
  readonly loading: boolean;
  readonly itemCount: number;
  readonly stale: boolean;
  readonly complete: boolean;
  readonly recovering: boolean;
  readonly failed: boolean;
}): OperationsViewState {
  if (!input.authorized) return "denied";
  if (input.loading) return "loading";
  if (input.failed) return "failure";
  if (input.recovering) return "recovery";
  if (!input.itemCount) return "empty";
  if (input.stale) return "stale";
  if (!input.complete) return "partial";
  return "ready";
}
