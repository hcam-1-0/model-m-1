import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { PlatformOperationsOverviewPage } from "../apps/operations-center/src/pages/platform-operations-overview-page";
describe("P5.6 Platform Operations", () => {
  it("renders generated qualified operations", () => {
    render(
      <MemoryRouter>
        <PlatformOperationsOverviewPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Platform operations" })).toBeInTheDocument();
    expect(screen.getByText(/not live telemetry/i)).toBeInTheDocument();
  });
});
