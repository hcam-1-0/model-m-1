import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router";
import { ProposedAlertQueuePage } from "../apps/intelligence-center/src/pages/proposed-alert-queue-page";
afterEach(cleanup);
describe("P5.4 proposed alerts", () => {
  it("distinguishes proposals from operational alerts and delivery", () => {
    render(
      <MemoryRouter>
        <ProposedAlertQueuePage />
      </MemoryRouter>,
    );
    expect(screen.getByText("Proposed alerts are not operational alerts.")).toBeVisible();
    expect(screen.getByText(/Priority means review order/)).toBeVisible();
    expect(screen.getByText("delivery identity: none")).toBeVisible();
  });
});
