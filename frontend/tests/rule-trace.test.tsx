import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { RuleTrace } from "../apps/intelligence-center/src/components/rule-trace";
import { generatedRuleTrace } from "../packages/intelligence-fixtures/src";
afterEach(cleanup);
describe("P5.4 exact rule trace", () => {
  it("renders every typed step and visible abstention", () => {
    render(<RuleTrace trace={generatedRuleTrace()} />);
    expect(screen.getByText("EXACT REVISIONED TRACE")).toBeVisible();
    expect(screen.getAllByRole("listitem")).toHaveLength(6);
    expect(screen.getAllByText("abstain")).not.toHaveLength(0);
    expect(screen.getByText(/Summaries are subordinate/)).toBeVisible();
  });
});
