import { describe, expect, it } from "vitest";
import {
  isSafeMediaDestination,
  isSafeMediaResourceDestination,
  renewPlayback,
  transitionPlayback,
  validatePlaybackGrant,
  validateSessionRequest,
  type PlaybackLease,
} from "@hcam/media-edge-contracts";
import { generatedPlaybackGrant } from "@hcam/test-fixtures";

const now = new Date("2026-09-08T09:00:30.000Z");
describe("P5.3 media security", () => {
  it("allows only generated relative session entry paths", () => {
    expect(
      isSafeMediaDestination(
        "/media-edge/sessions/SYN-SESSION-0001/master.m3u8",
        "http://127.0.0.1:4173",
      ),
    ).toBe(true);
    expect(
      isSafeMediaDestination("https://outside.invalid/master.m3u8", "http://127.0.0.1:4173"),
    ).toBe(false);
    expect(isSafeMediaDestination("//outside.invalid/master.m3u8", "http://127.0.0.1:4173")).toBe(
      false,
    );
    expect(
      isSafeMediaResourceDestination(
        "/media-edge/sessions/SYN-SESSION-0001/segment-20.ts",
        "http://127.0.0.1:4173",
      ),
    ).toBe(true);
    expect(
      isSafeMediaResourceDestination(
        "/media-edge/sessions/SYN-SESSION-0001/segment-20.ts?grant=x",
        "http://127.0.0.1:4173",
      ),
    ).toBe(false);
    expect(isSafeMediaDestination("relative", "http://127.0.0.1:4173")).toBe(false);
    expect(isSafeMediaDestination("/bad", "not-an-origin")).toBe(false);
    expect(
      isSafeMediaDestination(
        "/media-edge/sessions/SYN-SESSION-0001/master.m3u8#fragment",
        "http://127.0.0.1:4173",
      ),
    ).toBe(false);
    expect(
      isSafeMediaResourceDestination("https://outside.invalid/segment-20.ts", "not-an-origin"),
    ).toBe(false);
  });
  it("validates short-lived opaque grants and purpose-bound requests", () => {
    expect(validatePlaybackGrant(generatedPlaybackGrant(), now)).toBe(true);
    expect(validatePlaybackGrant({ ...generatedPlaybackGrant(), grant: "token" }, now)).toBe(false);
    expect(validatePlaybackGrant(null, now)).toBe(false);
    expect(validatePlaybackGrant("grant", now)).toBe(false);
    expect(validatePlaybackGrant({ ...generatedPlaybackGrant(), issuedAt: 1 }, now)).toBe(false);
    expect(validatePlaybackGrant({ ...generatedPlaybackGrant(), expiresAt: 1 }, now)).toBe(false);
    expect(validatePlaybackGrant({ ...generatedPlaybackGrant(), generated: false }, now)).toBe(
      false,
    );
    expect(validatePlaybackGrant({ ...generatedPlaybackGrant(), sessionRef: "bad" }, now)).toBe(
      false,
    );
    expect(validatePlaybackGrant({ ...generatedPlaybackGrant(), streamRef: "bad" }, now)).toBe(
      false,
    );
    expect(validatePlaybackGrant({ ...generatedPlaybackGrant(), mediaPath: "/bad" }, now)).toBe(
      false,
    );
    expect(validatePlaybackGrant({ ...generatedPlaybackGrant(), issuedAt: "invalid" }, now)).toBe(
      false,
    );
    expect(validatePlaybackGrant({ ...generatedPlaybackGrant(), expiresAt: "invalid" }, now)).toBe(
      false,
    );
    expect(
      validatePlaybackGrant(
        { ...generatedPlaybackGrant(), issuedAt: "2026-09-08T09:00:31.000Z" },
        now,
      ),
    ).toBe(false);
    expect(
      validatePlaybackGrant(
        { ...generatedPlaybackGrant(), expiresAt: "2026-09-08T09:00:30.000Z" },
        now,
      ),
    ).toBe(false);
    expect(
      validatePlaybackGrant(
        { ...generatedPlaybackGrant(), expiresAt: "2026-09-08T09:02:01.000Z" },
        now,
      ),
    ).toBe(false);
    expect(
      validateSessionRequest({
        streamRef: "SYN-STREAM-0001",
        departmentRef: "SYN-DEPT-01",
        purpose: "live_view",
        transportPreference: ["hls"],
        renditionCeiling: "low",
        reason: "Generated live view",
      }),
    ).toBe(true);
    const request = {
      streamRef: "SYN-STREAM-0001",
      departmentRef: "SYN-DEPT-01",
      purpose: "live_view",
      transportPreference: ["hls"],
      renditionCeiling: "low",
      reason: "Generated live view",
    };
    expect(validateSessionRequest(null)).toBe(false);
    expect(validateSessionRequest("request")).toBe(false);
    expect(validateSessionRequest({ ...request, streamRef: 1 })).toBe(false);
    expect(validateSessionRequest({ ...request, departmentRef: "bad" })).toBe(false);
    expect(validateSessionRequest({ ...request, purpose: "control" })).toBe(false);
    expect(validateSessionRequest({ ...request, transportPreference: [] })).toBe(false);
    expect(
      validateSessionRequest({
        ...request,
        transportPreference: ["hls", "whep", "native_hls", "hls"],
      }),
    ).toBe(false);
    expect(validateSessionRequest({ ...request, transportPreference: ["rtsp"] })).toBe(false);
    expect(validateSessionRequest({ ...request, renditionCeiling: "original" })).toBe(false);
    expect(validateSessionRequest({ ...request, reason: "short" })).toBe(false);
    expect(validateSessionRequest({ ...request, reason: "x".repeat(241) })).toBe(false);
  });
  it("enforces lifecycle transitions renewal bounds and idempotent close", () => {
    const lease: PlaybackLease = {
      sessionRef: "SYN-SESSION-0001",
      state: "playing",
      revision: 4,
      expiresAt: "2026-09-08T09:01:30.000Z",
      renewalCount: 0,
      closedAt: null,
    };
    const renewed = renewPlayback(lease, now);
    expect(renewed.renewalCount).toBe(1);
    expect(() => renewPlayback(renewed, now)).toThrow("playback_renewal_denied");
    const releasing = transitionPlayback(renewed, "releasing", now);
    const released = transitionPlayback(releasing, "released", now);
    expect(transitionPlayback(released, "released", now)).toBe(released);
    expect(() => transitionPlayback(lease, "idle", now)).toThrow("invalid_playback_transition");
    expect(() => renewPlayback({ ...lease, state: "failed" }, now)).toThrow(
      "playback_renewal_denied",
    );
    expect(() => renewPlayback(lease, now, 1_000)).toThrow("playback_renewal_denied");
    expect(() => renewPlayback(lease, now, 70_000)).toThrow("playback_renewal_denied");
  });
});
