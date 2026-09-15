import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router";
import { EvidenceReferenceTable } from "../apps/evidence-center/src/components/evidence-reference-table";
import { SourceBoundaryPanel } from "../apps/evidence-center/src/components/source-boundary-panel";
import { canResolveEvidenceSource, validateOpaqueSource } from "../packages/evidence-domain/src";
import { generatedEvidenceReferences } from "../packages/investigation-fixtures/src";
afterEach(cleanup);
describe("P5.5 evidence references", () => {
  it("keeps source references opaque and operations disabled", () => {
    const references = generatedEvidenceReferences(4);
    const first = references[0]!;
    expect(validateOpaqueSource(first.source)).toEqual([]);
    expect(canResolveEvidenceSource(first)).toBe(false);
    render(
      <MemoryRouter>
        <EvidenceReferenceTable items={references} />
        <SourceBoundaryPanel reference={first} />
      </MemoryRouter>,
    );
    expect(screen.getByRole("table")).toBeVisible();
    expect(screen.getByText("not exposed")).toBeVisible();
    expect(screen.getAllByText("unavailable").length).toBeGreaterThan(0);
  });
  it("rejects exposed operations, locators, and non-generated references", () => {
    const reference = generatedEvidenceReferences(1)[0]!;
    const hostile = {
      ...reference.source,
      referenceId: "REAL-REF",
      resolved: true,
      renderable: true,
      downloadable: true,
      locatorExposed: true,
      url: "discarded",
      token: "discarded",
    } as unknown as typeof reference.source;
    expect(validateOpaqueSource(hostile)).toEqual([
      "source_operation_enabled",
      "forbidden_key",
      "invalid_generated_reference",
    ]);
    expect(
      canResolveEvidenceSource({
        ...reference,
        sourceResolutionAuthorized: true,
      } as unknown as typeof reference),
    ).toBe(true);
  });
});
