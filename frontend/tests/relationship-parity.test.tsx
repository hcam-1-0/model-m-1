import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { GraphPanel } from "../apps/intelligence-center/src/components/graph-panel";
import { GraphTable } from "../apps/intelligence-center/src/components/graph-table";
import { NoGraphAdapterNotice, noGraphAdapter } from "../packages/relationship-renderers/src";
import { generatedRelationship } from "../packages/intelligence-fixtures/src";
afterEach(cleanup);
describe("P5.4 relationship parity", () => {
  it("keeps complete tables authoritative", () => {
    const value = generatedRelationship(10);
    render(
      <>
        <GraphPanel projection={value} />
        <GraphTable projection={noGraphAdapter.project(value)} />
        <NoGraphAdapterNotice />
      </>,
    );
    expect(screen.getByText("Relationship nodes")).toBeVisible();
    expect(screen.getByText("Relationship edges")).toBeVisible();
    expect(screen.getAllByRole("row")).toHaveLength(value.nodes.length + value.edges.length + 2);
    expect(noGraphAdapter.dependency).toBe("none");
    expect(screen.getByText(/Graph canvas is unavailable/)).toBeVisible();
  });
});
