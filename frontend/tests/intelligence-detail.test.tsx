import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router";
import { HypothesisDetailPage } from "../apps/intelligence-center/src/pages/hypothesis-detail-page";
afterEach(cleanup);
describe("P5.4 intelligence detail", () => {
  it("keeps proposition and evidence roles explicit", () => {
    render(
      <MemoryRouter initialEntries={["/intelligence/hypotheses/SYN-HYPOTHESIS-0001"]}>
        <HypothesisDetailPage />
      </MemoryRouter>,
    );
    expect(screen.getByText("WORKING ANALYTICAL PROPOSITION")).toBeVisible();
    expect(screen.getByText("Evidence composition")).toBeVisible();
    expect(screen.getByText("not established")).toBeVisible();
  });
});
