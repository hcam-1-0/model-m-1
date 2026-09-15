import { describe, expect, it } from "vitest";
import { admitRenderer, downgradeRenderer } from "@hcam/gis-domain";
import { limitsForProfile } from "@hcam/capabilities";
describe("renderer admission", () => {
  const base = {
    requested: "deck_interleaved" as const,
    profile: "control_room" as const,
    webgl: true,
    webgl2: true,
    policyAllowed: true,
    healthy: true,
  };
  it("fails closed for policy, health, and graphics limits", () => {
    expect(admitRenderer({ ...base, policyAllowed: false }).mode).toBe("list_only");
    expect(admitRenderer({ ...base, healthy: false }).reason).toBe("health_downgrade");
    expect(admitRenderer({ ...base, webgl: false }).reason).toBe("webgl_unavailable");
    expect(admitRenderer({ ...base, requested: "list_only" }).mode).toBe("list_only");
  });
  it("adapts to profile and WebGL2", () => {
    expect(admitRenderer({ ...base, profile: "low_resource" })).toMatchObject({
      mode: "maplibre",
      reason: "profile_limit",
    });
    expect(admitRenderer({ ...base, profile: "low_resource", requested: "maplibre" }).reason).toBe(
      "requested",
    );
    expect(admitRenderer({ ...base, webgl2: false }).mode).toBe("deck_overlaid");
    expect(admitRenderer({ ...base, profile: "enhanced" }).reason).toBe("profile_limit");
    expect(admitRenderer({ ...base, requested: "maplibre" }).mode).toBe("maplibre");
  });
  it("uses deterministic downgrade order", () => {
    expect(downgradeRenderer("deck_interleaved")).toBe("deck_overlaid");
    expect(downgradeRenderer("deck_overlaid")).toBe("maplibre");
    expect(downgradeRenderer("maplibre")).toBe("list_only");
    expect(downgradeRenderer("list_only")).toBe("list_only");
  });
  it("binds profile limits without changing authorization", () => {
    expect(limitsForProfile("low_resource")).toMatchObject({
      featureCap: 10,
      rendererCeiling: "maplibre",
      multiMonitor: false,
    });
    expect(limitsForProfile("enhanced").requestConcurrency).toBe(2);
    expect(limitsForProfile("control_room").rendererCeiling).toBe("deck_interleaved");
    expect(limitsForProfile("future_server").requestConcurrency).toBe(8);
  });
});
