import { describe, expect, it, vi } from "vitest";
import { createNativeHlsAdapter, createNoMediaAdapter } from "@hcam/media-adapters";
import { generatedPlaybackGrant } from "@hcam/test-fixtures";

describe("media teardown", () => {
  it("clears native media element state idempotently", async () => {
    const pause = vi.fn();
    const removeAttribute = vi.fn();
    const target = {
      canPlayType: () => "probably",
      pause,
      removeAttribute,
      load: vi.fn(),
      src: "",
    } as unknown as HTMLVideoElement;
    const adapter = createNativeHlsAdapter(
      generatedPlaybackGrant("SYN-STREAM-0001", "native_hls"),
      { now: () => new Date("2026-09-08T09:00:30.000Z") },
    );
    expect(await adapter.attach(target)).toEqual({ state: "attached", reason: "ready" });
    adapter.teardown();
    adapter.teardown();
    expect(pause).toHaveBeenCalledOnce();
    expect(removeAttribute).toHaveBeenCalledWith("src");
  });
  it("keeps no-media adapter harmless", async () => {
    const adapter = createNoMediaAdapter();
    expect(await adapter.attach({} as HTMLVideoElement)).toEqual({
      state: "unsupported",
      reason: "browser_unsupported",
    });
    expect(adapter.teardown()).toBeUndefined();
  });
  it("rejects invalid and unsupported native HLS before attachment", async () => {
    const unsupported = {
      canPlayType: () => "",
      pause: vi.fn(),
      removeAttribute: vi.fn(),
      load: vi.fn(),
    } as unknown as HTMLVideoElement;
    expect(
      await createNativeHlsAdapter(generatedPlaybackGrant("SYN-STREAM-0001", "native_hls"), {
        now: () => new Date("2026-09-08T09:00:30.000Z"),
      }).attach(unsupported),
    ).toEqual({ state: "unsupported", reason: "native_hls_unavailable" });
    const invalid = {
      ...generatedPlaybackGrant("SYN-STREAM-0001", "native_hls"),
      grant: "invalid",
    };
    const adapter = createNativeHlsAdapter(invalid, {
      now: () => new Date("2026-09-08T09:00:30.000Z"),
    });
    expect(await adapter.attach(unsupported)).toEqual({ state: "denied", reason: "grant_invalid" });
    adapter.teardown();
  });
  it("uses browser defaults with a currently valid native grant", async () => {
    const timestamp = Date.now();
    const grant = {
      ...generatedPlaybackGrant("SYN-STREAM-0001", "native_hls"),
      issuedAt: new Date(timestamp - 1_000).toISOString(),
      expiresAt: new Date(timestamp + 60_000).toISOString(),
    };
    const target = {
      canPlayType: () => "probably",
      pause: vi.fn(),
      removeAttribute: vi.fn(),
      load: vi.fn(),
    } as unknown as HTMLVideoElement;
    const adapter = createNativeHlsAdapter(grant);
    expect(await adapter.attach(target)).toEqual({ state: "attached", reason: "ready" });
    adapter.teardown();
  });
  it("keeps the native adapter deterministic without a browser global", () => {
    vi.stubGlobal("window", undefined);
    try {
      const adapter = createNativeHlsAdapter(
        generatedPlaybackGrant("SYN-STREAM-0001", "native_hls"),
        { origin: "http://127.0.0.1:4173" },
      );
      expect(adapter.transport).toBe("native_hls");
      adapter.teardown();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});
