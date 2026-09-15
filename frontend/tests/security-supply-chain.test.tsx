import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SupplyChainAssurancePage } from "../apps/security-center/src/pages/supply-chain-assurance-page";
describe("P5.6 supply chain", () => {
  it("keeps scanners unavailable", () => {
    render(<SupplyChainAssurancePage />);
    expect(screen.getByRole("heading", { name: "Supply-chain assurance" })).toBeInTheDocument();
    expect(screen.getAllByText("Not executed").length).toBeGreaterThan(0);
  });
});
