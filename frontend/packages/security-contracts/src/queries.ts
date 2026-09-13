export interface SecurityQuery {
  readonly departmentRef: string;
  readonly lane: string;
  readonly state: string;
  readonly cursor: string | null;
  readonly limit: 10 | 25 | 50;
}
export function securityQueryKey(query: SecurityQuery): readonly string[] {
  return [
    "p5-6",
    "security",
    query.departmentRef,
    query.lane,
    query.state,
    query.cursor ?? "first",
    String(query.limit),
  ];
}
