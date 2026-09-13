import {
  authorizationHeaders,
  isSafeMediaDestination,
  validatePlaybackGrant,
  type PlaybackSessionGrant,
} from "@hcam/media-edge-contracts";
import type { MediaAdapter } from "./index";
import { discardMediaSignal, type SignalSink } from "./telemetry";

export interface WhepAdapterOptions {
  readonly enabled: boolean;
  readonly timeoutMs?: number;
  readonly now?: () => Date;
  readonly origin?: string;
  readonly fetcher?: typeof fetch;
  readonly createPeer?: () => RTCPeerConnection;
  readonly fallback?: () => MediaAdapter;
  readonly signal?: SignalSink;
}
export function createWhepAdapter(
  grant: PlaybackSessionGrant,
  options: WhepAdapterOptions,
): MediaAdapter {
  const now = options.now ?? (() => new Date());
  const defaultOrigin =
    typeof window === "undefined" ? "http://127.0.0.1:4173" : window.location.origin;
  const origin = options.origin ?? defaultOrigin;
  const fetcher = options.fetcher ?? fetch;
  const createPeer = options.createPeer ?? (() => new RTCPeerConnection());
  const signal = options.signal ?? discardMediaSignal;
  let peer: RTCPeerConnection | null = null;
  let fallback: MediaAdapter | null = null;
  let video: HTMLVideoElement | null = null;
  let resource: string | null = null;
  const attachFallback = async (target: HTMLVideoElement, reason: string) => {
    peer?.close();
    peer = null;
    resource = null;
    if (!options.fallback) return { state: "fallback" as const, reason };
    fallback = options.fallback();
    signal({ name: "fallback", transport: "whep", reason, durationBand: "none" });
    return fallback.attach(target);
  };
  return {
    transport: "whep",
    async attach(target) {
      if (!options.enabled) return attachFallback(target, "whep_disabled");
      if (!validatePlaybackGrant(grant, now()) || !isSafeMediaDestination(grant.mediaPath, origin))
        return { state: "denied", reason: "grant_invalid" };
      peer = createPeer();
      video = target;
      peer.addTransceiver("video", { direction: "recvonly" });
      peer.ontrack = (event) => {
        const stream = event.streams[0];
        if (video && stream) video.srcObject = stream;
      };
      const offer = await peer.createOffer();
      await peer.setLocalDescription(offer);
      if (!offer.sdp || offer.sdp.length > 65_536)
        return attachFallback(target, "whep_offer_rejected");
      const controller = new AbortController();
      const timer = setTimeout(
        () => controller.abort(),
        Math.min(Math.max(options.timeoutMs ?? 8_000, 1_000), 10_000),
      );
      let response: Response;
      try {
        response = await fetcher(grant.mediaPath, {
          method: "POST",
          headers: {
            ...authorizationHeaders(grant),
            Accept: "application/sdp",
            "Content-Type": "application/sdp",
          },
          body: offer.sdp,
          cache: "no-store",
          credentials: "same-origin",
          redirect: "error",
          referrerPolicy: "no-referrer",
          signal: controller.signal,
        });
      } catch {
        return await attachFallback(target, "whep_transport_failed");
      } finally {
        clearTimeout(timer);
      }
      if (response.status !== 201) {
        return attachFallback(target, "whep_negotiation_failed");
      }
      if (!(response.headers.get("Content-Type") ?? "").toLowerCase().startsWith("application/sdp"))
        return attachFallback(target, "whep_content_type_rejected");
      const location = response.headers.get("Location");
      if (location && !isSafeMediaDestination(location, origin)) {
        peer.close();
        peer = null;
        return { state: "denied", reason: "whep_location_rejected" };
      }
      resource = location;
      const answer = await response.text();
      if (!answer || answer.length > 65_536) return attachFallback(target, "whep_answer_rejected");
      await peer.setRemoteDescription({ type: "answer", sdp: answer });
      signal({ name: "session_started", transport: "whep", reason: "ready", durationBand: "none" });
      return { state: "attached", reason: "ready" };
    },
    teardown() {
      const deleteTarget = resource;
      fallback?.teardown();
      fallback = null;
      peer?.close();
      peer = null;
      if (video) video.srcObject = null;
      video = null;
      resource = null;
      if (deleteTarget && isSafeMediaDestination(deleteTarget, origin))
        void fetcher(deleteTarget, {
          method: "DELETE",
          headers: authorizationHeaders(grant),
          cache: "no-store",
          credentials: "same-origin",
          redirect: "error",
          referrerPolicy: "no-referrer",
        }).catch(() => undefined);
      signal({
        name: "teardown",
        transport: "whep",
        reason: "teardown_complete",
        durationBand: "none",
      });
    },
  };
}
