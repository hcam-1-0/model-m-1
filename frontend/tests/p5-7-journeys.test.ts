import { describe, expect, it } from "vitest";
import {
  journeyDefinitions,
  qualitySurfaces,
  type QualitySurface,
} from "../packages/quality-contracts/src";
import { p57GeneratedCases } from "../packages/quality-fixtures/src";

describe("P5.7 cross-portal journeys", () => {
  it("covers all journeys, surfaces, and mandatory authority boundaries", () => {
    for (const journey of journeyDefinitions) {
      expect(journey.surfaces.length).toBeGreaterThan(1);
      expect(p57GeneratedCases.some((item) => item.journeyId === journey.id)).toBe(true);
    }
    for (const surface of qualitySurfaces)
      expect(
        journeyDefinitions.some((journey) =>
          (journey.surfaces as readonly QualitySurface[]).includes(surface),
        ),
      ).toBe(true);
    expect(
      p57GeneratedCases
        .filter(({ expected }) => expected === "remain_non_effective")
        .every(({ authority }) => authority === "non_effective"),
    ).toBe(true);
  });
});
