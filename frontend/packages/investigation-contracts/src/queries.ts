export interface InvestigationQuery {
  readonly departmentRef: string;
  readonly purposeCode: string;
  readonly cursor: string | null;
  readonly limit: 10 | 25 | 50;
  readonly state?: string;
  readonly kind?: string;
  readonly chronology: "record" | "event_context";
}
export function investigationQueryKey(query: InvestigationQuery): readonly string[] {
  return [
    "p5-5",
    query.departmentRef,
    query.purposeCode,
    query.cursor ?? "first",
    String(query.limit),
    query.state ?? "all",
    query.kind ?? "all",
    query.chronology,
  ];
}
