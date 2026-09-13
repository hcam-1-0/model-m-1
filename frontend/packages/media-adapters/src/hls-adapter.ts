import type Hls from "hls.js";
import type { ErrorTypes, Events, HlsConfig } from "hls.js";
import {
  authorizationHeaders,
  isSafeMediaDestination,
  isSafeMediaResourceDestination,
  validatePlaybackGrant,
  type PlaybackSessionGrant,
} from "@hcam/media-edge-contracts";
import type { MediaAdapter, MediaAttachResult } from "./index";
import { discardMediaSignal, type SignalSink } from "./telemetry";

export interface HlsAdapterOptions {
  readonly now?: () => Date;
  readonly origin?: string;
  readonly signal?: SignalSink;
  readonly create?: (config: Partial<HlsConfig>) => Hls;
  readonly loadModule?: () => Promise<{
    readonly default: typeof Hls;
    readonly ErrorTypes: typeof ErrorTypes;
    readonly Events: typeof Events;
  }>;
}
export function createHlsAdapter(
  grant: PlaybackSessionGrant,
  options: HlsAdapterOptions = {},
): MediaAdapter {
  const now = options.now ?? (() => new Date());
  const defaultOrigin =
    typeof window === "undefined" ? "http://127.0.0.1:4173" : window.location.origin;
  const origin = options.origin ?? defaultOrigin;
  const signal = options.signal ?? discardMediaSignal;
  let instance: Hls | null = null;
  let video: HTMLVideoElement | null = null;
  return {
    transport: "hls",
    async attach(target): Promise<MediaAttachResult> {
      if (!validatePlaybackGrant(grant, now()) || !isSafeMediaDestination(grant.mediaPath, origin))
        return { state: "denied", reason: "grant_invalid" };
      const module = await (options.loadModule ?? (() => import("hls.js")))();
      if (!module.default.isSupported()) return { state: "unsupported", reason: "mse_unavailable" };
      video = target;
      const create = options.create ?? ((config) => new module.default(config));
      instance = create({
        autoStartLoad: true,
        capLevelToPlayerSize: true,
        enableWorker: true,
        maxBufferLength: 12,
        backBufferLength: 0,
        maxBufferSize: 24 * 1024 * 1024,
        xhrSetup(xhr, url) {
          if (!isSafeMediaResourceDestination(url, origin)) {
            xhr.abort();
            throw new Error("media_resource_destination_rejected");
          }
          for (const [name, value] of Object.entries(authorizationHeaders(grant)))
            xhr.setRequestHeader(name, value);
        },
      });
      instance.attachMedia(target);
      instance.once(module.Events.MEDIA_ATTACHED, () => instance?.loadSource(grant.mediaPath));
      instance.on(module.Events.MANIFEST_PARSED, () =>
        signal({
          name: "manifest_loaded",
          transport: "hls",
          reason: "ready",
          durationBand: "none",
        }),
      );
      instance.on(module.Events.ERROR, (_event, data) => {
        if (data.type === module.ErrorTypes.MEDIA_ERROR && data.fatal) {
          signal({
            name: "stalled",
            transport: "hls",
            reason: "stream_stalled",
            durationBand: "none",
          });
          instance?.recoverMediaError();
        }
      });
      signal({
        name: "session_started",
        transport: "hls",
        reason: "generated_only",
        durationBand: "none",
      });
      return { state: "attached", reason: "ready" };
    },
    teardown() {
      instance?.stopLoad();
      instance?.detachMedia();
      instance?.destroy();
      instance = null;
      if (video) {
        video.pause();
        video.removeAttribute("src");
        video.load();
      }
      video = null;
      signal({
        name: "teardown",
        transport: "hls",
        reason: "teardown_complete",
        durationBand: "none",
      });
    },
  };
}
