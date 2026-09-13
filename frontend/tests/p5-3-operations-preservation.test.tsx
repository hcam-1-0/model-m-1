import { describe, expect, it } from "vitest";
import { operationsRoutes } from "../apps/operations-center/src/routes";
describe("P5.3 operations preservation", () => {
  it("keeps every accepted camera and live route", () => {
    expect(operationsRoutes.slice(0, 4)).toEqual([
      ["/operations", "Camera catalogue"],
      ["/operations/live", "Live workspace"],
      ["/operations/wall", "Monitor wall"],
      ["/operations/workspaces", "Workspaces"],
    ]);
  });
});
