import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ReconstructionPanel } from "../apps/investigation-center/src/components/reconstruction-panel";
import { RevisionComparison } from "../apps/investigation-center/src/components/revision-comparison";
import { compareRevisions } from "../packages/investigation-domain/src";
import { generatedReconstruction } from "../packages/investigation-fixtures/src";
afterEach(cleanup);
describe("P5.5 reconstruction", () => {
  it("shows exact revision, digest, omissions, and later-state warning", () => {
    const before = generatedReconstruction(7, "partial");
    render(
      <>
        <ReconstructionPanel value={before} />
        <RevisionComparison value={compareRevisions(before, generatedReconstruction(8))} />
      </>,
    );
    expect(screen.getByText("Reconstruction SYN-REV-0007")).toBeVisible();
    expect(screen.getByText(/Later records exist/)).toBeVisible();
    expect(screen.getByRole("columnheader", { name: "Meaning" })).toBeVisible();
  });
  it("covers added, removed, unchanged, and incomplete comparison semantics", () => {
    const before = generatedReconstruction(7, "complete");
    const same = { ...generatedReconstruction(8, "complete"), timeline: before.timeline };
    const added = generatedReconstruction(8, "complete");
    const removed = {
      ...generatedReconstruction(8, "complete"),
      timeline: before.timeline.slice(2),
    };
    const partial = { ...same, completeness: "partial" as const };
    expect(compareRevisions(before, same)).toMatchObject({
      complete: true,
      limitations: [],
      changes: [
        { field: "timeline_entries", meaning: "unchanged" },
        { field: "completeness", meaning: "unchanged" },
      ],
    });
    expect(compareRevisions(before, added).changes[0]?.meaning).toBe("added");
    expect(compareRevisions(before, removed).changes[0]?.meaning).toBe("removed");
    expect(compareRevisions(before, partial)).toMatchObject({
      complete: false,
      limitations: ["At least one generated revision is incomplete."],
      changes: [{ meaning: "unchanged" }, { meaning: "changed" }],
    });
  });
});
