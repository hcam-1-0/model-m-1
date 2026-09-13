import type {
  AdmissionDecision,
  AdmissionBudget,
  AdmissionRequest,
  BrowserMediaCapabilities,
  MediaTransport,
  RenditionBand,
  ResourceProfileId,
} from "./contracts";
import { getResourceProfile } from "./profiles";

const renditionRank: Readonly<Record<RenditionBand, number>> = { low: 0, medium: 1, high: 2 };
const intentRank = {
  single: 7,
  incident: 6,
  pinned: 5,
  selected: 4,
  visible: 3,
  near: 2,
  hidden: 1,
} as const;
const healthRank = { healthy: 4, attention: 3, unknown: 2, critical: 1 } as const;
function chooseRendition(requested: RenditionBand, ceiling: RenditionBand): RenditionBand {
  return renditionRank[requested] <= renditionRank[ceiling] ? requested : ceiling;
}
export function selectTransport(
  requested: MediaTransport,
  capabilities: BrowserMediaCapabilities,
  whepEnabled: boolean,
): MediaTransport {
  if (requested === "whep" && whepEnabled && capabilities.webrtc) return "whep";
  if (capabilities.mse) return "hls";
  if (capabilities.nativeHls) return "native_hls";
  return "none";
}
export function admitStreams(
  profileId: ResourceProfileId,
  requests: readonly AdmissionRequest[],
  capabilities: BrowserMediaCapabilities,
  whepEnabled = false,
  budget: AdmissionBudget = {
    decodeUnits: Number.MAX_SAFE_INTEGER,
    networkUnits: Number.MAX_SAFE_INTEGER,
    serverUnits: Number.MAX_SAFE_INTEGER,
  },
): readonly AdmissionDecision[] {
  const profile = getResourceProfile(profileId);
  const ordered = [...requests].sort(
    (left, right) =>
      Number(right.focused) - Number(left.focused) ||
      Number(right.pinned) - Number(left.pinned) ||
      intentRank[right.intent ?? "visible"] - intentRank[left.intent ?? "visible"] ||
      Number(right.visible) - Number(left.visible) ||
      healthRank[right.health ?? "unknown"] - healthRank[left.health ?? "unknown"] ||
      right.priority - left.priority ||
      left.streamId.localeCompare(right.streamId),
  );
  let decodeUsed = 0;
  let networkUsed = 0;
  let serverUsed = 0;
  return ordered.map((request, index) => {
    const transport = selectTransport(request.requestedTransport, capabilities, whepEnabled);
    const decode = Math.max(1, request.decodeUnits ?? 1);
    const network = Math.max(1, request.networkUnits ?? 1);
    const server = Math.max(1, request.serverUnits ?? 1);
    const resourceAvailable =
      decodeUsed + decode <= budget.decodeUnits &&
      networkUsed + network <= budget.networkUnits &&
      serverUsed + server <= budget.serverUnits;
    const withinBudget = index < profile.maxStreams && request.visible && resourceAvailable;
    const admitted = withinBudget && transport !== "none";
    if (admitted) {
      decodeUsed += decode;
      networkUsed += network;
      serverUsed += server;
    }
    return {
      streamId: request.streamId,
      admitted,
      transport: admitted ? transport : "none",
      rendition: admitted
        ? chooseRendition(request.requestedRendition, profile.preferredRendition)
        : null,
      rank: index + 1,
      reason: !request.visible
        ? "profile_budget_exceeded"
        : transport === "none"
          ? "browser_unsupported"
          : withinBudget
            ? transport !== request.requestedTransport
              ? "fallback_to_hls"
              : "ready"
            : "profile_budget_exceeded",
    };
  });
}
