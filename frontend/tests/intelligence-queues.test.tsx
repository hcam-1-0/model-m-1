import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router";
import { QueueTable } from "../apps/intelligence-center/src/components/queue-table";
import { generatedQueue } from "../packages/intelligence-fixtures/src";
afterEach(cleanup);
describe("P5.4 queues", () => {
  it("renders the authoritative typed queue", () => {
    render(
      <MemoryRouter>
        <QueueTable
          items={generatedQueue("hypothesis", 10).items}
          detailBase="/intelligence/hypotheses"
        />
      </MemoryRouter>,
    );
    expect(screen.getAllByRole("row")).toHaveLength(11);
    expect(screen.getAllByText("Working hypothesis")).toHaveLength(10);
  });
  it("renders an explicit empty state", () => {
    render(
      <MemoryRouter>
        <QueueTable items={[]} detailBase="/intelligence/hypotheses" />
      </MemoryRouter>,
    );
    expect(screen.getByText("No generated items match")).toBeVisible();
  });
});
