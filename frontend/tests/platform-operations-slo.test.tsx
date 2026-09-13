import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SloErrorBudgetPage } from "../apps/operations-center/src/pages/slo-error-budget-page";
describe("P5.6 SLO projections", () => {
  it("prevents production-target claims", () => {
    render(<SloErrorBudgetPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: "SLO and error budgets" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Not a production target")).toHaveLength(8);
  });
});
