import { describe, expect, it } from "vitest";
import { evaluateHardBudget } from "../packages/quality-domain/src";

describe("P5.7 hard performance budgets", () => {
  const budget = {
    metric: "interaction_ms",
    maximum: 200,
    context: "generated_local_Edge_V04_C1",
  } as const;

  it("passes only measurements inside the frozen contextual maximum", () => {
    expect(evaluateHardBudget(199, budget).status).toBe("pass");
    expect(evaluateHardBudget(201, budget).reason).toBe("hard_budget_exceeded");
    expect(evaluateHardBudget(Number.NaN, budget).reason).toBe("contract_invalid");
    expect(evaluateHardBudget(-1, budget).reason).toBe("contract_invalid");
  });
});
