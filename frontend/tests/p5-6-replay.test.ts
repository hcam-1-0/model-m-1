import { describe, expect, it } from "vitest";
import {
  deterministicReplayDigest,
  p56ContractCases,
} from "../packages/admin-security-operations-fixtures/src";
describe("P5.6 deterministic replay", () => {
  it("replays exactly 1120 cases in stable order", () => {
    expect(p56ContractCases).toHaveLength(1120);
    expect(p56ContractCases[0]?.ref).toBe("SYN-P56-CASE-0001");
    expect(p56ContractCases.at(-1)?.ref).toBe("SYN-P56-CASE-1120");
    expect(deterministicReplayDigest(p56ContractCases)).toBe(
      deterministicReplayDigest([...p56ContractCases]),
    );
  });
});
