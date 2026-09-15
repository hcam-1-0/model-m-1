import type { ImpactTarget } from "../../investigation-contracts/src";

export interface ImpactClosure {
  readonly total: number;
  readonly applied: number;
  readonly pending: number;
  readonly blocked: number;
  readonly failed: number;
  readonly superseded: number;
  readonly complete: boolean;
}
export function summarizeImpactClosure(targets: readonly ImpactTarget[]): ImpactClosure {
  const count = (status: ImpactTarget["status"]) =>
    targets.filter((target) => target.status === status).length;
  const pending = count("pending");
  const blocked = count("blocked");
  const failed = count("failed");
  return {
    total: targets.length,
    applied: count("applied"),
    pending,
    blocked,
    failed,
    superseded: count("superseded"),
    complete: targets.length > 0 && pending + blocked + failed === 0,
  };
}
