import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router";
vi.mock("@hcam/gis-renderers", () => ({
  mountMapLibre: () => ({
    focus: () => true,
    dispose: () => undefined,
    map: { addControl: () => undefined },
  }),
}));
import { App } from "../apps/command-center/src/app";
afterEach(() => cleanup());
describe("Command Center", () => {
  it("renders the primary generated situation and connected GIS", () => {
    render(
      <MemoryRouter initialEntries={["/command"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { level: 1, name: "Command overview" })).toBeVisible();
    expect(screen.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
    expect(screen.getAllByText(/Generated/).length).toBeGreaterThan(1);
    expect(screen.getAllByRole("link", { name: /Open GIS Center/ })[0]).toBeVisible();
    expect(screen.getByText("Blocked producer gaps")).toBeVisible();
  });
  it("supports route and theme interactions", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/command"]}>
        <App />
      </MemoryRouter>,
    );
    await user.click(screen.getByRole("link", { name: "Coverage" }));
    expect(screen.getByRole("heading", { level: 1, name: "Coverage" })).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Change theme" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    const navigationToggle = screen.getByRole("button", { name: "Open navigation" });
    await user.click(navigationToggle);
    expect(navigationToggle).toHaveAccessibleName("Close navigation");
    expect(navigationToggle).toHaveAttribute("aria-expanded", "true");
  });
});
