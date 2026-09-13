import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RetentionPolicyProjectionsPage } from "../apps/admin-center/src/pages/retention-policy-projections-page";
describe("P5.6 retention previews", () => {
  it("renders generated non-operative projections", () => {
    render(<RetentionPolicyProjectionsPage />);
    expect(
      screen.getByRole("heading", { name: "Retention policy projections" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Unavailable").length).toBeGreaterThan(0);
  });
});
