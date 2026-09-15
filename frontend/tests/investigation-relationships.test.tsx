import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { InvestigationRelationshipPanel } from "../apps/investigation-center/src/components/investigation-relationship-panel";
import { InvestigationRelationshipTable } from "../apps/investigation-center/src/components/investigation-relationship-table";
import { boundRelationships } from "../packages/investigation-domain/src";
import { generatedProvenance } from "../packages/investigation-fixtures/src";
afterEach(cleanup);
describe("P5.5 investigation relationships", () => {
  it("keeps bounded visual and authoritative tables aligned", () => {
    const projection = generatedProvenance(10);
    expect(
      boundRelationships(projection.nodes, projection.edges, 12, 24).authoritativeRepresentation,
    ).toBe("node_edge_tables");
    render(
      <>
        <InvestigationRelationshipPanel projection={projection} />
        <InvestigationRelationshipTable projection={projection} />
      </>,
    );
    expect(screen.getByLabelText("Bounded relationship visual")).toBeVisible();
    expect(screen.getAllByRole("table").length).toBeGreaterThan(0);
    expect(screen.getByText(/Authoritative node and edge tables/)).toBeVisible();
  });
  it("reports truncation and removes edges outside the bounded node set", () => {
    const projection = generatedProvenance(50);
    const bounded = boundRelationships(projection.nodes, projection.edges, 12, 24);
    expect(bounded.nodes).toHaveLength(12);
    expect(
      bounded.edges.every((edge) => bounded.nodes.some((node) => node.ref === edge.toRef)),
    ).toBe(true);
    expect(bounded.truncated).toBe(true);
    expect(boundRelationships([], [], 12, 24).truncated).toBe(false);
  });
});
