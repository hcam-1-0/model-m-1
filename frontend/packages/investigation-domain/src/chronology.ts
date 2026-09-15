import type { TimelineEntry } from "../../investigation-contracts/src";

export interface ChronologyProjection {
  readonly mode: "record" | "event_context";
  readonly entries: readonly TimelineEntry[];
  readonly authority: "record_sequence";
  readonly qualified: boolean;
  readonly warning: string | null;
}
export function recordChronology(entries: readonly TimelineEntry[]): ChronologyProjection {
  return {
    mode: "record",
    entries: [...entries].sort((left, right) => left.recordSequence - right.recordSequence),
    authority: "record_sequence",
    qualified: true,
    warning: null,
  };
}
export function eventContextChronology(entries: readonly TimelineEntry[]): ChronologyProjection {
  const sorted = [...entries].sort((left, right) => {
    const leftTime = left.eventTime.value
      ? Date.parse(left.eventTime.value)
      : Number.MAX_SAFE_INTEGER;
    const rightTime = right.eventTime.value
      ? Date.parse(right.eventTime.value)
      : Number.MAX_SAFE_INTEGER;
    return leftTime - rightTime || left.recordSequence - right.recordSequence;
  });
  return {
    mode: "event_context",
    entries: sorted,
    authority: "record_sequence",
    qualified: true,
    warning: "Event time is qualified context. Record sequence remains authoritative.",
  };
}
export function chronologyHasUncertainty(entries: readonly TimelineEntry[]): boolean {
  return entries.some(
    (entry) =>
      entry.eventTime.value === null ||
      entry.eventTime.precision === "unknown" ||
      entry.eventTime.clockCondition !== "synchronized",
  );
}
