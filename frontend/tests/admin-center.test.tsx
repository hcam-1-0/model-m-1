import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { AdminRoutes } from "../apps/admin-center/src/routes";
describe("P5.6 Admin Center", () => {
  it("renders the generated administration overview", () => {
    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AdminRoutes />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Administration overview" })).toBeInTheDocument();
    expect(screen.getByText("Server decisions only")).toBeInTheDocument();
    expect(screen.getAllByText(/generated/i).length).toBeGreaterThan(0);
  });
});
