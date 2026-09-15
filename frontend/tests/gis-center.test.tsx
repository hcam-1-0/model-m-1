import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router";
const focus = vi.fn(() => true);
const fit = vi.fn(() => true);
vi.mock("@hcam/gis-renderers", () => ({
  mountMapLibre: () => ({
    focus,
    fit,
    dispose: () => undefined,
    map: { addControl: () => undefined },
  }),
  createDeckOverlay: () => Promise.resolve({}),
}));
vi.mock("../apps/gis-center/src/components/gujarat-operations-map", () => ({
  GujaratOperationsMap: ({ onCameraSelect }: { onCameraSelect: (camera: unknown) => void }) => (
    <button
      type="button"
      data-testid="gujarat-operations-map"
      onClick={() =>
        onCameraSelect({
          id: "HCAM-AMD-001",
          name: "Riverfront Gate",
          zone: "Ahmedabad Central",
          type: "Fixed",
          ownership: "H-CAM Operations",
          status: "online",
          lastUpdated: "Just now",
          coordinates: [72.5813, 23.0314],
          previewAvailability: "available",
        })
      }
    >
      Generated Gujarat map
    </button>
  ),
}));
import { App } from "../apps/gis-center/src/app";
beforeEach(() => {
  vi.stubGlobal(
    "WebGLRenderingContext",
    class WebGLRenderingContext {
      readonly generated = true;
    },
  );
  vi.stubGlobal(
    "WebGL2RenderingContext",
    class WebGL2RenderingContext {
      readonly generated = true;
    },
  );
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
describe("GIS Center", () => {
  it("renders connected GIS with authoritative fallback", () => {
    render(
      <MemoryRouter initialEntries={["/gis"]}>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { level: 1, name: "GIS overview" })).toBeVisible();
    expect(screen.getByRole("navigation", { name: "GIS Center navigation" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Generated spatial records" })).toBeVisible();
    expect(screen.getByText("External sources")).toBeVisible();
    expect(screen.getByText("Disabled")).toBeVisible();
    expect(screen.getByRole("link", { name: "New display window" })).toHaveAttribute(
      "href",
      "http://127.0.0.1:4174/gis",
    );
  });
  it("filters, selects, and changes safe modes", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/gis"]}>
        <App />
      </MemoryRouter>,
    );
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Filter source state" }),
      "unknown",
    );
    expect(screen.getByText("2 records")).toBeVisible();
    await user.selectOptions(screen.getByRole("combobox", { name: "Filter source state" }), "all");
    await user.click(screen.getByRole("button", { name: "Fit generated extent" }));
    expect(fit).toHaveBeenCalled();
    const filter = screen.getByRole("textbox", { name: "Filter generated map records" });
    await user.type(filter, "A-1");
    expect(screen.getByText("1 records")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Generated sector A-1" }));
    expect(screen.getByRole("heading", { name: "Generated sector A-1" })).toBeVisible();
    await user.selectOptions(screen.getByRole("combobox", { name: "Renderer" }), "list_only");
    expect(screen.getByText(/Map renderer unavailable/)).toBeVisible();
    const navigationToggle = screen.getByRole("button", { name: "Open GIS navigation" });
    await user.click(navigationToggle);
    expect(navigationToggle).toHaveAccessibleName("Close GIS navigation");
    expect(navigationToggle).toHaveAttribute("aria-expanded", "true");
  });
  it("merges the Gujarat operations workspace without losing portal navigation", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/gis/map"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("region", { name: "Gujarat operational map" }, { timeout: 5_000 }),
    ).toBeVisible();
    expect(screen.getByRole("navigation", { name: "GIS Center navigation" })).toBeVisible();
    expect(screen.getByText("Riverfront Gate")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Camera status filters" }));
    expect(screen.getByText("Filter the map")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Operational alerts" }));
    expect(screen.getByText("Priority queue")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Preview access policy" }));
    expect(screen.getByText("Operator policy")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Map display controls" }));
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Operational map renderer" }),
      "list_only",
    );
    expect(screen.getByRole("heading", { name: "Map renderer is not admitted" })).toBeVisible();
    expect(
      screen.getByRole("region", { name: "Authoritative list-only operational map fallback" }),
    ).toBeVisible();
  }, 20_000);
});
