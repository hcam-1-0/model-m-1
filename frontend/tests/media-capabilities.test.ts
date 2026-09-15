import { describe, expect, it } from "vitest";
import { mapExecutionClassToCameraProfile } from "@hcam/capabilities";
import { detectBrowserMediaCapabilities, durationBand } from "@hcam/media-adapters";

describe("media capabilities", () => {
  it("detects MSE WebRTC and native HLS without activating them", () => {
    const video = { canPlayType: (type: string) => (type.includes("mpegurl") ? "maybe" : "") };
    const MediaSourceStub = { isTypeSupported: () => true } as unknown as typeof MediaSource;
    class PeerStub {
      readonly generated = true;
    }
    expect(
      detectBrowserMediaCapabilities(video, {
        MediaSource: MediaSourceStub,
        RTCPeerConnection: PeerStub as unknown as typeof RTCPeerConnection,
      }),
    ).toEqual({ mse: true, nativeHls: true, webrtc: true, codecs: ["avc1.42E01E"] });
  });
  it("fails closed when browser media APIs are absent", () => {
    expect(detectBrowserMediaCapabilities(null, {})).toEqual({
      mse: false,
      nativeHls: false,
      webrtc: false,
      codecs: [],
    });
  });
  it("uses low-cardinality duration bands", () => {
    expect(durationBand(Number.NaN)).toBe("none");
    expect(durationBand(500)).toBe("under_1s");
    expect(durationBand(5000)).toBe("1_to_5s");
    expect(durationBand(5001)).toBe("over_5s");
  });
  it("maps every Phase 3 execution class through the server authorization ceiling", () => {
    expect(mapExecutionClassToCameraProfile("portable_cpu", false)).toBe("low_resource");
    expect(mapExecutionClassToCameraProfile("portable_cpu", true)).toBe("enhanced_workstation");
    expect(mapExecutionClassToCameraProfile("owned_gpu_lab", true)).toBe("owned_gpu_lab");
    expect(mapExecutionClassToCameraProfile("standalone_server", true)).toBe("future_server");
    expect(mapExecutionClassToCameraProfile("kubernetes_cluster", true)).toBe("future_server");
  });
});
