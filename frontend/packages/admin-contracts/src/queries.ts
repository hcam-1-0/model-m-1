export interface AdminQuery {
  readonly departmentRef: string;
  readonly resource: string;
  readonly state: string;
  readonly cursor: string | null;
  readonly limit: 10 | 25 | 50;
}
export function adminQueryKey(query: AdminQuery): readonly string[] {
  return [
    "p5-6",
    "admin",
    query.departmentRef,
    query.resource,
    query.state,
    query.cursor ?? "first",
    String(query.limit),
  ];
}
export const adminQueryScopes = Object.freeze([
  "admin.organizations",
  "admin.identities",
  "admin.roles",
  "admin.changes",
  "admin.governance",
  "admin.configuration",
] as const);
