export * from "./adapter";
export * from "./no-graph-adapter";
export * from "./table-renderer";

export function boundedTableParity(input: {
  readonly visualCount: number;
  readonly tableCount: number;
  readonly truncated: boolean;
  readonly tableAuthoritative: boolean;
}): boolean {
  return (
    input.tableAuthoritative &&
    input.tableCount >= input.visualCount &&
    (!input.truncated || input.tableCount > input.visualCount)
  );
}
