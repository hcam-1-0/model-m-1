import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { QueuesWorkersCircuitsPage } from "../apps/operations-center/src/pages/queues-workers-circuits-page";
describe("P5.6 queue operations", () => {
  it("shows lease and dead-letter state", () => {
    render(<QueuesWorkersCircuitsPage />);
    expect(
      screen.getByRole("heading", { name: "Queues, workers, and circuits" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("fail closed").length).toBeGreaterThan(0);
  });
});
