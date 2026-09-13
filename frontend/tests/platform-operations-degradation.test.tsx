import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DegradationKillSwitchPage } from "../apps/operations-center/src/pages/degradation-kill-switch-page";
describe("P5.6 degradation controls", () => {
  it("keeps kill switches non-operative", () => {
    render(<DegradationKillSwitchPage />);
    expect(screen.getByRole("button", { name: "Change state" })).toBeDisabled();
    expect(screen.getByText("Automatic activation")).toBeInTheDocument();
  });
});
