import type { BrowserMediaCapabilities } from "@hcam/camera-live-domain";

export function detectBrowserMediaCapabilities(
  video: Pick<HTMLVideoElement, "canPlayType"> | null,
  environment: {
    readonly MediaSource?: typeof MediaSource;
    readonly RTCPeerConnection?: typeof RTCPeerConnection;
  } = globalThis,
): BrowserMediaCapabilities {
  const nativeHls = Boolean(video?.canPlayType("application/vnd.apple.mpegurl"));
  const mse = Boolean(environment.MediaSource?.isTypeSupported('video/mp4; codecs="avc1.42E01E"'));
  return {
    mse,
    nativeHls,
    webrtc: typeof environment.RTCPeerConnection === "function",
    codecs: mse || nativeHls ? ["avc1.42E01E"] : [],
  };
}
