import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SpatialIntelligencePanel } from "../apps/intelligence-center/src/components/spatial-intelligence-panel";
import { generatedSpatial } from "../packages/intelligence-fixtures/src";
afterEach(cleanup);
describe("P5.4 spatial intelligence", () => {
  it("synchronizes generated visual and authoritative table selection", () => {
    const select = vi.fn();
    const value = generatedSpatial(10);
    render(
      <SpatialIntelligencePanel
        projection={value}
        selected={value.records[0]!.ref}
        onSelect={select}
      />,
    );
    expect(screen.getByText("no tile network")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "2" }));
    expect(select).toHaveBeenCalledWith(value.records[1]!.ref);
    expect(screen.getAllByRole("row")).toHaveLength(11);
  });
});
