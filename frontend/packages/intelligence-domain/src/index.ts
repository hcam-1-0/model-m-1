export * from "./commands";
export * from "./corrections";
export * from "./lifecycle";
export * from "./profiles";
export * from "./reasons";
export * from "./receipts";
export * from "./semantic";
export * from "./state";

export function permitsInvestigationHandoff(input: {
  readonly reviewRecorded: boolean;
  readonly departmentMatches: boolean;
  readonly sourceOperational: boolean;
}): boolean {
  return input.reviewRecorded && input.departmentMatches && !input.sourceOperational;
}
