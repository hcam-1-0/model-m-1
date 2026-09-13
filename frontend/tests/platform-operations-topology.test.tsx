import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TopologyProjectionsPage } from "../apps/operations-center/src/pages/topology-projections-page";
describe("P5.6 topology projections", () => {
  it("shows all six undeployed profiles", () => {
    render(<TopologyProjectionsPage />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Topology projections" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/Not deployed/)).toHaveLength(6);
  });
});
