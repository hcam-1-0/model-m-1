import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { SecurityRoutes } from "../apps/security-center/src/routes";
describe("P5.6 Security Center", () => {
  it("renders qualified security posture", () => {
    render(
      <MemoryRouter initialEntries={["/security"]}>
        <SecurityRoutes />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Security overview" })).toBeInTheDocument();
    expect(screen.getByText("Assurance boundary")).toBeInTheDocument();
  });
});
