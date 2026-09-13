import {
  isSafeMediaDestination,
  validatePlaybackGrant,
  type PlaybackSessionGrant,
} from "@hcam/media-edge-contracts";
import type { MediaAdapter } from "./index";
import { discardMediaSignal, type SignalSink } from "./telemetry";

export function createNativeHlsAdapter(
  grant: PlaybackSessionGrant,
  options: {
    readonly now?: () => Date;
    readonly origin?: string;
    readonly signal?: SignalSink;
  } = {},
): MediaAdapter {
  const now = options.now ?? (() => new Date());
  const defaultOrigin =
    typeof window === "undefined" ? "http://127.0.0.1:4173" : window.location.origin;
  const origin = options.origin ?? defaultOrigin;
  const signal = options.signal ?? discardMediaSignal;
  let video: HTMLVideoElement | null = null;
  return {
    transport: "native_hls",
    attach(target) {
      if (!validatePlaybackGrant(grant, now()) || !isSafeMediaDestination(grant.mediaPath, origin))
        return Promise.resolve({ state: "denied" as const, reason: "grant_invalid" });
      if (!target.canPlayType("application/vnd.apple.mpegurl"))
        return Promise.resolve({ state: "unsupported" as const, reason: "native_hls_unavailable" });
      video = target;
      target.src = grant.mediaPath;
      target.load();
      signal({
        name: "session_started",
        transport: "native_hls",
        reason: "ready",
        durationBand: "none",
      });
      return Promise.resolve({ state: "attached" as const, reason: "ready" });
    },
    teardown() {
      if (video) {
        video.pause();
        video.removeAttribute("src");
        video.load();
      }
      video = null;
      signal({
        name: "teardown",
        transport: "native_hls",
        reason: "teardown_complete",
        durationBand: "none",
      });
    },
  };
}
