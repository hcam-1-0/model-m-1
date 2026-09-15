import { cleanup, render } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router";
import { App } from "../apps/operations-center/src/app";

afterEach(cleanup);
describe("P5.3 accessibility", () => {
  it("has no critical generated catalogue violations", async () => {
    const { container } = render(
      <MemoryRouter initialEntries={["/operations"]}>
        <App />
      </MemoryRouter>,
    );
    const result = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    expect(result.violations).toEqual([]);
  });
  it("retains skip navigation and authoritative status text", () => {
    const { getByRole, getByText } = render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    expect(getByRole("link", { name: "Skip to main content" })).toHaveAttribute(
      "href",
      "#main-content",
    );
    expect(getByText("Generated environment. No operational data.")).toBeInTheDocument();
  });
});
