import type { QueueKind } from "./contracts";

export interface IntelligenceQuery {
  readonly queue: QueueKind;
  readonly departmentRef: string;
  readonly cursor: string | null;
  readonly limit: 10 | 25 | 50;
  readonly state?: string;
  readonly priority?: string;
}
export function canonicalQueryKey(query: IntelligenceQuery): readonly string[] {
  return [
    "p5-4",
    query.departmentRef,
    query.queue,
    query.cursor ?? "first",
    String(query.limit),
    query.state ?? "all",
    query.priority ?? "all",
  ];
}
