import { describe, expect, it } from "vitest";
import {
  p56AdministrationRoutes,
  p56PlatformOperationsRoutes,
  p56SecurityRoutes,
} from "@hcam/navigation";
describe("P5.6 center handoffs", () => {
  it("keeps Command primary and specialist routes typed", () => {
    expect(p56AdministrationRoutes).toHaveLength(9);
    expect(p56SecurityRoutes).toHaveLength(9);
    expect(p56PlatformOperationsRoutes).toHaveLength(9);
    expect(p56AdministrationRoutes.every((item) => item.portalId === "admin")).toBe(true);
  });
});
