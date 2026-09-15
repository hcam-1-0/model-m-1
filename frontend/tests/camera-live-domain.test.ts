import { describe, expect, it } from "vitest";
import {
  cameraListState,
  safeReason,
  serializeHandoff,
  streamState,
  validateHandoff,
  isGeneratedCameraProjection,
} from "@hcam/camera-live-domain";
import { generatedCameras } from "@hcam/test-fixtures";

const now = new Date("2026-09-08T09:02:00.000Z");
describe("camera live domain", () => {
  it("accepts only bounded generated camera projections", () => {
    const camera = generatedCameras(1)[0]!;
    expect(isGeneratedCameraProjection(camera)).toBe(true);
    expect(isGeneratedCameraProjection({ ...camera, id: "REAL-1" })).toBe(false);
    expect(isGeneratedCameraProjection(null)).toBe(false);
    expect(isGeneratedCameraProjection("camera")).toBe(false);
    expect(isGeneratedCameraProjection({ ...camera, generated: false })).toBe(false);
    expect(isGeneratedCameraProjection({ ...camera, id: 1 })).toBe(false);
    expect(isGeneratedCameraProjection({ ...camera, label: "" })).toBe(false);
    expect(isGeneratedCameraProjection({ ...camera, label: "x".repeat(121) })).toBe(false);
    expect(isGeneratedCameraProjection({ ...camera, departmentRef: "outside" })).toBe(false);
    expect(isGeneratedCameraProjection({ ...camera, streams: "invalid" })).toBe(false);
    expect(isGeneratedCameraProjection({ ...camera, streams: Array.from({ length: 5 }) })).toBe(
      false,
    );
    expect(isGeneratedCameraProjection({ ...camera, state: "invalid" })).toBe(false);
    expect(isGeneratedCameraProjection({ ...camera, health: "invalid" })).toBe(false);
  });
  it("projects explicit catalogue and stream states", () => {
    const cameras = generatedCameras(10);
    expect(cameraListState(null, now)).toBe("loading");
    expect(cameraListState([], now)).toBe("empty");
    expect(cameraListState(cameras, now)).toBe("partial");
    expect(
      cameraListState(
        cameras.map((camera) => ({
          ...camera,
          freshness: { ...camera.freshness, staleAt: "2026-09-08T09:01:00.000Z" },
        })),
        now,
      ),
    ).toBe("stale");
    expect(
      cameraListState(
        cameras.map((camera) => ({ ...camera, state: "unknown" as const })),
        now,
      ),
    ).toBe("unknown");
    expect(
      cameraListState(
        cameras.map((camera) => ({
          ...camera,
          state: "offline" as const,
          freshness: { ...camera.freshness, staleAt: "2026-09-08T10:00:00.000Z" },
        })),
        now,
      ),
    ).toBe("failure");
    expect(streamState(cameras[0]!.streams[0]!, "department_denied")).toBe("denied");
    expect(streamState(cameras[0]!.streams[0]!, "producer_unavailable")).toBe("degraded");
    expect(streamState({ ...cameras[0]!.streams[0]!, state: "blocked" }, null)).toBe("degraded");
    expect(streamState({ ...cameras[0]!.streams[0]!, state: "stale" }, null)).toBe("stale");
    expect(streamState({ ...cameras[0]!.streams[0]!, state: "unavailable" }, null)).toBe("failure");
    expect(streamState({ ...cameras[0]!.streams[0]!, health: "unknown" }, null)).toBe("unknown");
    expect(streamState({ ...cameras[0]!.streams[0]!, health: "attention" }, null)).toBe("partial");
    expect(
      cameraListState(
        cameras.map((camera) => ({
          ...camera,
          state: "online" as const,
          freshness: { ...camera.freshness, staleAt: "2026-09-08T10:00:00.000Z" },
        })),
        now,
      ),
    ).toBe("ready");
  });
  it("validates and serializes opaque handoffs", () => {
    const handoff = {
      contractVersion: "1.0.0",
      cameraRef: "SYN-CAM-0001",
      streamRef: "SYN-STREAM-0001",
      departmentRef: "SYN-DEPT-01",
      sourceRevision: "SYN-REV-001",
      expiresAt: "2026-09-08T09:04:00.000Z",
      purpose: "view_generated_camera",
    } as const;
    expect(validateHandoff(handoff, now)).toBe(true);
    expect(decodeURIComponent(serializeHandoff(handoff))).toContain("SYN-CAM-0001");
    expect(validateHandoff({ ...handoff, expiresAt: "2026-09-08T09:01:00.000Z" }, now)).toBe(false);
    expect(validateHandoff(null, now)).toBe(false);
    expect(validateHandoff("handoff", now)).toBe(false);
    expect(validateHandoff({ ...handoff, contractVersion: "2.0.0" }, now)).toBe(false);
    expect(validateHandoff({ ...handoff, cameraRef: 1 }, now)).toBe(false);
    expect(validateHandoff({ ...handoff, streamRef: null }, now)).toBe(true);
    expect(validateHandoff({ ...handoff, streamRef: 1 }, now)).toBe(false);
    expect(validateHandoff({ ...handoff, departmentRef: 1 }, now)).toBe(false);
    expect(validateHandoff({ ...handoff, sourceRevision: 1 }, now)).toBe(false);
    expect(validateHandoff({ ...handoff, purpose: "control" }, now)).toBe(false);
    expect(validateHandoff({ ...handoff, expiresAt: 1 }, now)).toBe(false);
    expect(() => serializeHandoff({ ...handoff, cameraRef: "BAD" })).toThrow(
      "invalid_generated_handoff",
    );
  });
  it("maps unknown reasons to a safe label", () => {
    expect(safeReason("ready")).toBe("ready");
    expect(safeReason("raw provider failure at 10.0.0.1")).toBe("producer_unavailable");
  });
});
