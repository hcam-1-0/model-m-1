import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CustodyTable } from "../apps/evidence-center/src/components/custody-table";
import { ProvenancePanel } from "../apps/evidence-center/src/components/provenance-panel";
import { ProvenanceTable } from "../apps/evidence-center/src/components/provenance-table";
import {
  custodyIsIndependent,
  validateProvenanceProjection,
} from "../packages/evidence-domain/src";
import {
  generatedCustodyEvents,
  generatedProvenance,
} from "../packages/investigation-fixtures/src";
afterEach(cleanup);
describe("P5.5 evidence provenance and custody", () => {
  it("validates bounded provenance and separate custody", () => {
    const projection = generatedProvenance(10);
    const custody = generatedCustodyEvents();
    expect(validateProvenanceProjection(projection)).toEqual([]);
    expect(custodyIsIndependent(custody, projection)).toBe(true);
    render(
      <>
        <ProvenancePanel projection={projection} />
        <ProvenanceTable projection={projection} />
        <CustodyTable events={custody} />
      </>,
    );
    expect(screen.getByLabelText("Generated provenance visual projection")).toBeVisible();
    expect(screen.getAllByRole("table")).toHaveLength(2);
  });
  it("rejects unbounded, dangling, non-authoritative, and external provenance", () => {
    const projection = generatedProvenance(1);
    const hostile = {
      ...projection,
      nodes: Array.from({ length: 13 }, (_, index) => ({
        ...projection.nodes[0]!,
        ref: `SYN-PROV-HOSTILE-${index}` as never,
      })),
      edges: Array.from({ length: 25 }, (_, index) => ({
        ...projection.edges[0]!,
        ref: `SYN-EDGE-HOSTILE-${index}` as never,
        fromRef: "SYN-MISSING" as never,
      })),
      authoritativeRepresentation: "visual_only",
      externalProvImport: true,
      provConformanceClaim: true,
    } as unknown as typeof projection;
    expect(validateProvenanceProjection(hostile)).toEqual([
      "node_ceiling_exceeded",
      "edge_ceiling_exceeded",
      "dangling_edge",
      "table_authority_missing",
      "external_prov_boundary_violation",
    ]);
    expect(custodyIsIndependent(generatedCustodyEvents(2), projection)).toBe(false);
    expect(
      custodyIsIndependent(
        generatedCustodyEvents().map((event, index) =>
          index === 0
            ? ({ ...event, inferredFromProvenance: true } as unknown as typeof event)
            : event,
        ),
        projection,
      ),
    ).toBe(false);
  });
});
