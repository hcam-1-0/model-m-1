import { describe, expect, it } from "vitest";
import {
  boundedTimeWindow,
  limitWorkItems,
  situationState,
  sortWorkItems,
  validateSituationSnapshot,
} from "@hcam/command-domain";
import type { SituationSnapshot } from "@hcam/command-domain";
import { generatedGisFeatures, generatedSituationSnapshot } from "@hcam/test-fixtures";
describe("P5.2 deterministic replay", () => {
  it("replays generated fixtures identically", () => {
    expect(generatedGisFeatures(50)).toEqual(generatedGisFeatures(50));
    expect(generatedSituationSnapshot(10)).toEqual(generatedSituationSnapshot(10));
    expect(() => generatedGisFeatures(0)).toThrow("invalid_generated_feature_count");
    expect(() => generatedGisFeatures(51)).toThrow("invalid_generated_feature_count");
  });
  it("sorts server-authored bands without scoring", () => {
    const snapshot = generatedSituationSnapshot(10) as SituationSnapshot;
    const sorted = sortWorkItems(snapshot.workItems);
    expect(sorted[0]!.band).toBe("critical");
    expect(limitWorkItems(snapshot.workItems, 3)).toHaveLength(3);
    expect(() => limitWorkItems(snapshot.workItems, 0)).toThrow();
    expect(() => limitWorkItems(snapshot.workItems, 101)).toThrow();
  });
  it("validates projection and bounded windows", () => {
    const snapshot = generatedSituationSnapshot(10) as SituationSnapshot;
    expect(validateSituationSnapshot(snapshot)).toBe(true);
    expect(validateSituationSnapshot({ ...snapshot, unavailableProducers: [] })).toBe(false);
    for (const invalid of [
      null,
      { ...snapshot, contractVersion: "2.0.0" },
      { ...snapshot, marker: "NOT-GENERATED" },
      { ...snapshot, departmentRef: 42 },
      { ...snapshot, departmentRef: "bad-department" },
      { ...snapshot, metrics: null },
      { ...snapshot, metrics: Array.from({ length: 25 }, () => snapshot.metrics[0]) },
      { ...snapshot, workItems: null },
      { ...snapshot, workItems: Array.from({ length: 101 }, () => snapshot.workItems[0]) },
      { ...snapshot, activity: null },
      { ...snapshot, activity: Array.from({ length: 101 }, () => snapshot.activity[0]) },
      { ...snapshot, unavailableProducers: null },
    ]) {
      expect(validateSituationSnapshot(invalid)).toBe(false);
    }
    expect(boundedTimeWindow(Number.NaN)).toBe(1);
    expect(boundedTimeWindow(-2)).toBe(1);
    expect(boundedTimeWindow(100)).toBe(24);
    expect(boundedTimeWindow(3.4)).toBe(3);
  });
  it("reports truth states in precedence order", () => {
    const snapshot = generatedSituationSnapshot(10) as SituationSnapshot;
    expect(situationState(null, new Date())).toBe("loading");
    expect(
      situationState({ ...snapshot, metrics: [], workItems: [] }, new Date("2026-09-08T00:20:00Z")),
    ).toBe("empty");
    expect(situationState(snapshot, new Date("2026-09-08T00:20:00Z"))).toBe("correction");
    const noCorrection = {
      ...snapshot,
      activity: snapshot.activity.filter((item: { kind: string }) => item.kind !== "correction"),
    };
    expect(situationState(noCorrection, new Date("2026-09-08T02:00:00Z"))).toBe("stale");
    expect(
      situationState(
        { ...noCorrection, freshness: { ...noCorrection.freshness, completeness: "unknown" } },
        new Date("2026-09-08T00:20:00Z"),
      ),
    ).toBe("unknown");
    expect(situationState(noCorrection, new Date("2026-09-08T00:20:00Z"))).toBe("partial");
    expect(
      situationState(
        {
          ...noCorrection,
          unavailableProducers: [],
          freshness: { ...noCorrection.freshness, completeness: "complete" },
        },
        new Date("2026-09-08T00:20:00Z"),
      ),
    ).toBe("ready");
  });
});
