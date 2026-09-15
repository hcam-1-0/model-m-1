import { describe, expect, it, vi } from "vitest";
import { createNoMediaAdapter, createWhepAdapter } from "@hcam/media-adapters";
import { generatedPlaybackGrant } from "@hcam/test-fixtures";

function peer(close = vi.fn(), offerSdp: string | undefined = "v=0\r\n") {
  const candidate = {
    addTransceiver: vi.fn(),
    createOffer: vi.fn(() => Promise.resolve({ type: "offer", sdp: offerSdp })),
    setLocalDescription: vi.fn(() => Promise.resolve()),
    setRemoteDescription: vi.fn(() => Promise.resolve()),
    close,
    ontrack: null,
  };
  return candidate as unknown as RTCPeerConnection;
}
const video = { srcObject: null } as unknown as HTMLVideoElement;
describe("default-off WHEP adapter", () => {
  it("uses deterministic HLS fallback when the kill switch is off", async () => {
    const fallback = {
      transport: "hls" as const,
      attach: vi.fn(() => Promise.resolve({ state: "attached" as const, reason: "ready" })),
      teardown: vi.fn(),
    };
    const result = await createWhepAdapter(generatedPlaybackGrant("SYN-STREAM-0001", "whep"), {
      enabled: false,
      fallback: () => fallback,
    }).attach(video);
    expect(result).toEqual({ state: "attached", reason: "ready" });
    expect(fallback.attach).toHaveBeenCalledOnce();
  });
  it("negotiates one bounded generated session and deletes it during teardown", async () => {
    const close = vi.fn();
    const fakePeer = peer(close);
    const fetcher = vi.fn((_input: RequestInfo | URL, init?: RequestInit) =>
      Promise.resolve(
        init?.method === "DELETE"
          ? new Response(null, { status: 204 })
          : new Response("v=0\r\n", {
              status: 201,
              headers: {
                "Content-Type": "application/sdp",
                Location: "/media-edge/sessions/SYN-SESSION-0001/whep",
              },
            }),
      ),
    );
    const adapter = createWhepAdapter(generatedPlaybackGrant("SYN-STREAM-0001", "whep"), {
      enabled: true,
      now: () => new Date("2026-09-08T09:00:30.000Z"),
      origin: "http://127.0.0.1:4173",
      fetcher,
      createPeer: () => fakePeer,
    });
    expect(await adapter.attach(video)).toEqual({ state: "attached", reason: "ready" });
    const remoteStream = {} as MediaStream;
    fakePeer.ontrack?.({ streams: [remoteStream] } as unknown as RTCTrackEvent);
    expect(video.srcObject).toBe(remoteStream);
    fakePeer.ontrack?.({ streams: [] } as unknown as RTCTrackEvent);
    adapter.teardown();
    expect(close).toHaveBeenCalledOnce();
    expect(fetcher).toHaveBeenLastCalledWith(
      "/media-edge/sessions/SYN-SESSION-0001/whep",
      expect.objectContaining({ method: "DELETE", redirect: "error" }),
    );
  });
  it("falls back on invalid response types without retaining raw SDP", async () => {
    const fallback = createNoMediaAdapter("hls_unavailable");
    const adapter = createWhepAdapter(generatedPlaybackGrant("SYN-STREAM-0001", "whep"), {
      enabled: true,
      now: () => new Date("2026-09-08T09:00:30.000Z"),
      fetcher: vi.fn(() =>
        Promise.resolve(
          new Response("not-sdp", { status: 201, headers: { "Content-Type": "text/plain" } }),
        ),
      ),
      createPeer: peer,
      fallback: () => fallback,
    });
    expect(await adapter.attach(video)).toEqual({
      state: "unsupported",
      reason: "hls_unavailable",
    });
  });
  it.each([
    ["whep_offer_rejected", () => peer(vi.fn(), undefined), () => Promise.resolve(new Response())],
    ["whep_transport_failed", peer, () => Promise.reject(new Error("generated transport failure"))],
    ["whep_negotiation_failed", peer, () => Promise.resolve(new Response(null, { status: 503 }))],
    [
      "whep_content_type_rejected",
      peer,
      () => Promise.resolve(new Response("v=0\r\n", { status: 201 })),
    ],
    [
      "whep_answer_rejected",
      peer,
      () =>
        Promise.resolve(
          new Response("", {
            status: 201,
            headers: { "Content-Type": "application/sdp" },
          }),
        ),
    ],
  ] as const)(
    "classifies %s and tears down through fallback",
    async (reason, createPeer, fetcher) => {
      const fallback = createNoMediaAdapter(reason);
      const adapter = createWhepAdapter(generatedPlaybackGrant("SYN-STREAM-0001", "whep"), {
        enabled: true,
        now: () => new Date("2026-09-08T09:00:30.000Z"),
        fetcher,
        createPeer,
        fallback: () => fallback,
      });
      expect(await adapter.attach(video)).toEqual({ state: "unsupported", reason });
      adapter.teardown();
    },
  );
  it("denies invalid grants and hostile resource locations", async () => {
    const invalid = createWhepAdapter(
      { ...generatedPlaybackGrant("SYN-STREAM-0001", "whep"), grant: "invalid" },
      { enabled: true, createPeer: peer },
    );
    expect(await invalid.attach(video)).toEqual({ state: "denied", reason: "grant_invalid" });

    const close = vi.fn();
    const hostile = createWhepAdapter(generatedPlaybackGrant("SYN-STREAM-0001", "whep"), {
      enabled: true,
      now: () => new Date("2026-09-08T09:00:30.000Z"),
      origin: "http://127.0.0.1:4173",
      createPeer: () => peer(close),
      fetcher: () =>
        Promise.resolve(
          new Response("v=0\r\n", {
            status: 201,
            headers: {
              "Content-Type": "application/sdp",
              Location: "https://outside.invalid/whep",
            },
          }),
        ),
    });
    expect(await hostile.attach(video)).toEqual({
      state: "denied",
      reason: "whep_location_rejected",
    });
    expect(close).toHaveBeenCalledOnce();
    hostile.teardown();
  });
  it("returns a typed fallback result when no fallback adapter is configured", async () => {
    const adapter = createWhepAdapter(generatedPlaybackGrant("SYN-STREAM-0001", "whep"), {
      enabled: false,
    });
    expect(await adapter.attach(video)).toEqual({ state: "fallback", reason: "whep_disabled" });
    adapter.teardown();
  });
  it("rejects oversized offers and missing response content types", async () => {
    const fallback = createNoMediaAdapter("hls_unavailable");
    const oversized = createWhepAdapter(generatedPlaybackGrant("SYN-STREAM-0001", "whep"), {
      enabled: true,
      now: () => new Date("2026-09-08T09:00:30.000Z"),
      createPeer: () => peer(vi.fn(), "x".repeat(65_537)),
      fallback: () => fallback,
    });
    expect(await oversized.attach(video)).toEqual({
      state: "unsupported",
      reason: "hls_unavailable",
    });
    const missingType = createWhepAdapter(generatedPlaybackGrant("SYN-STREAM-0001", "whep"), {
      enabled: true,
      now: () => new Date("2026-09-08T09:00:30.000Z"),
      timeoutMs: 500,
      createPeer: peer,
      fetcher: () => Promise.resolve(new Response(null, { status: 201 })),
      fallback: () => fallback,
    });
    expect(await missingType.attach(video)).toEqual({
      state: "unsupported",
      reason: "hls_unavailable",
    });
  });
  it("uses the browser peer factory and safely tears down before attachment", async () => {
    const previous = globalThis.RTCPeerConnection;
    const close = vi.fn();
    function GeneratedPeer() {
      return peer(close);
    }
    globalThis.RTCPeerConnection = GeneratedPeer as unknown as typeof RTCPeerConnection;
    try {
      const adapter = createWhepAdapter(generatedPlaybackGrant("SYN-STREAM-0001", "whep"), {
        enabled: true,
        now: () => new Date("2026-09-08T09:00:30.000Z"),
        timeoutMs: 20_000,
        fetcher: () =>
          Promise.resolve(
            new Response("v=0\r\n", {
              status: 201,
              headers: { "Content-Type": "application/sdp" },
            }),
          ),
      });
      expect(await adapter.attach(video)).toEqual({ state: "attached", reason: "ready" });
      adapter.teardown();
      expect(close).toHaveBeenCalledOnce();
    } finally {
      globalThis.RTCPeerConnection = previous;
    }
    createWhepAdapter(generatedPlaybackGrant("SYN-STREAM-0001", "whep"), {
      enabled: true,
      createPeer: peer,
    }).teardown();
  });
});
