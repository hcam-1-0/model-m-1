import { cleanup, render } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router";
import { IntelligenceOverviewPage } from "../apps/intelligence-center/src/pages/intelligence-overview-page";
import { MandatoryReviewDeskPage } from "../apps/intelligence-center/src/pages/mandatory-review-desk-page";
import { RelationshipExplorerPage } from "../apps/intelligence-center/src/pages/relationship-explorer-page";
afterEach(cleanup);
describe("P5.4 accessibility", () => {
  it.each([
    ["overview", IntelligenceOverviewPage],
    ["review", MandatoryReviewDeskPage],
    ["relationship", RelationshipExplorerPage],
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
