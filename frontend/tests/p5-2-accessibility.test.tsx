import { cleanup, render } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router";
vi.mock("@hcam/gis-renderers", () => ({
  mountMapLibre: () => ({
    focus: () => true,
    dispose: () => undefined,
    map: { addControl: () => undefined },
  }),
  createDeckOverlay: () => Promise.resolve({}),
}));
import { App as CommandApp } from "../apps/command-center/src/app";
import { App as GisApp } from "../apps/gis-center/src/app";
afterEach(() => cleanup());
describe("P5.2 accessibility", () => {
  it.each([
    ["command", CommandApp],
    ["gis", GisApp],
  ] as const)("has no critical %s violations", async (_name, Component) => {
    const { container } = render(
      <MemoryRouter>
        <Component />
      </MemoryRouter>,
    );
    const result = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    expect(result.violations).toEqual([]);
  });
});
