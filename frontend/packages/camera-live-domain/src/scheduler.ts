import type { AdmissionDecision, CameraReason } from "./contracts";

export interface RecoveryState {
  readonly attempts: number;
  readonly firstFailureAt: number;
  readonly cooldownUntil: number;
  readonly circuitOpenUntil: number;
}
export interface RecoveryDecision {
  readonly retry: boolean;
  readonly delayMs: number;
  readonly reason: CameraReason;
}
const retryDelays = [1_000, 3_000, 10_000] as const;
export function nextRecovery(state: RecoveryState, now: number): RecoveryDecision {
  if (now < state.circuitOpenUntil)
    return { retry: false, delayMs: state.circuitOpenUntil - now, reason: "circuit_open" };
  if (now < state.cooldownUntil)
    return { retry: false, delayMs: state.cooldownUntil - now, reason: "cooldown_active" };
  if (state.attempts >= retryDelays.length)
    return { retry: false, delayMs: 60_000, reason: "circuit_open" };
  const delayMs = retryDelays[state.attempts];
  if (delayMs === undefined) return { retry: false, delayMs: 60_000, reason: "circuit_open" };
  return { retry: true, delayMs, reason: "stream_stalled" };
}
export function scheduleAdmissions(
  decisions: readonly AdmissionDecision[],
): readonly AdmissionDecision[] {
  return [...decisions].sort(
    (left, right) => Number(right.admitted) - Number(left.admitted) || left.rank - right.rank,
  );
}
