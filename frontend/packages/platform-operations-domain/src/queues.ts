import type { QueueHealth } from "../../operations-contracts/src";
export type QueueDisposition = "normal" | "watch" | "recovering" | "fail_closed" | "unknown";
export function queueDisposition(queue: QueueHealth): QueueDisposition {
  if (queue.leaseState === "expired" || queue.deadLetterBand === "present") return "fail_closed";
  if (queue.leaseState === "recovering") return "recovering";
  if (queue.depthBand === "unknown" || queue.oldestAgeBand === "unknown") return "unknown";
  if (queue.depthBand === "high" || queue.retryBand === "elevated") return "watch";
  return "normal";
}
export const workerPolicy = Object.freeze({
  leaseSeconds: 90,
  boundedRetries: 3,
  abandonedWorkRecovery: true,
  gracefulShutdown: true,
  deadLetterRequired: true,
} as const);
