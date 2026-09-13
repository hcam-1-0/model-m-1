import { cleanup, render } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router";
import { EvidenceOverviewPage } from "../apps/evidence-center/src/pages/evidence-overview-page";
import { ProvenanceCustodyPage } from "../apps/evidence-center/src/pages/provenance-custody-page";
import { InvestigationOverviewPage } from "../apps/investigation-center/src/pages/investigation-overview-page";
import { InvestigationTimelinePage } from "../apps/investigation-center/src/pages/investigation-timeline-page";
afterEach(cleanup);
describe("P5.5 accessibility", () => {
  it.each([
    ["investigation overview", InvestigationOverviewPage],
    ["timeline", InvestigationTimelinePage],
    ["evidence overview", EvidenceOverviewPage],
    ["provenance custody", ProvenanceCustodyPage],
  ] as const)(
    "has no critical %s violations",
    async (_name, Component) => {
      const { container } = render(
        <MemoryRouter>
          <Component />
        </MemoryRouter>,
      );
      const result = await axe.run(container, {
        rules: { "color-contrast": { enabled: false } },
      });
      expect(result.violations).toEqual([]);
    },
    20_000,
  );
});
