export interface OperationsQuery {
  readonly departmentRef: string;
  readonly domain: string;
  readonly state: string;
  readonly cursor: string | null;
  readonly limit: 10 | 25 | 50;
}
export function operationsQueryKey(query: OperationsQuery): readonly string[] {
  return [
    "p5-6",
    "operations",
    query.departmentRef,
    query.domain,
    query.state,
    query.cursor ?? "first",
    String(query.limit),
  ];
}
