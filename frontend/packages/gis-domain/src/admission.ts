import type { ResourceProfile } from "@hcam/capabilities";
import type { GisAdmission, GisRendererMode } from "@hcam/gis-contracts";

export interface RendererInputs {
  readonly requested: GisRendererMode;
  readonly profile: ResourceProfile;
  readonly webgl: boolean;
  readonly webgl2: boolean;
  readonly policyAllowed: boolean;
  readonly healthy: boolean;
}
export function admitRenderer(input: RendererInputs): GisAdmission {
  if (!input.policyAllowed)
    return { admitted: false, mode: "list_only", reason: "policy_denied", listFallback: true };
  if (!input.healthy)
    return { admitted: false, mode: "list_only", reason: "health_downgrade", listFallback: true };
  if (input.requested === "list_only")
    return { admitted: true, mode: "list_only", reason: "requested", listFallback: true };
  if (!input.webgl)
    return { admitted: false, mode: "list_only", reason: "webgl_unavailable", listFallback: true };
  if (input.profile === "low_resource")
    return {
      admitted: true,
      mode: "maplibre",
      reason: input.requested === "maplibre" ? "requested" : "profile_limit",
      listFallback: true,
    };
  if (
    input.requested === "deck_interleaved" &&
    (!input.webgl2 || (input.profile !== "control_room" && input.profile !== "future_server"))
  )
    return {
      admitted: true,
      mode: "deck_overlaid",
      reason: input.webgl2 ? "profile_limit" : "webgl2_unavailable",
      listFallback: true,
    };
  return { admitted: true, mode: input.requested, reason: "requested", listFallback: true };
}
export function downgradeRenderer(mode: GisRendererMode): GisRendererMode {
  if (mode === "deck_interleaved") return "deck_overlaid";
  if (mode === "deck_overlaid") return "maplibre";
  return "list_only";
}
