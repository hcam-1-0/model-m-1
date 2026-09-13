import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ChronologySwitcher } from "../apps/investigation-center/src/components/chronology-switcher";
import { TimelineTable } from "../apps/investigation-center/src/components/timeline-table";
import { generatedTimelinePage } from "../packages/investigation-fixtures/src";
afterEach(cleanup);
describe("P5.5 investigation timeline", () => {
  it("renders record sequence as authoritative", () => {
    const page = generatedTimelinePage(12);
    render(
      <>
        <ChronologySwitcher mode="record" onChange={() => undefined} />
        <TimelineTable entries={page.items} />
      </>,
    );
    expect(screen.getByRole("button", { name: /Record sequence/i })).toBeVisible();
    expect(screen.getByRole("table")).toBeVisible();
    expect(
      screen.getAllByText(
        /Generated analytical record|Generated append-only chronology record|Generated human-review record/,
      ).length,
    ).toBeGreaterThan(0);
  });
});
