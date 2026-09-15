import { describe, expect, it } from "vitest";
import {
  admitStreams,
  clampRequestedStreams,
  getResourceProfile,
  nextRecovery,
  scheduleAdmissions,
  selectTransport,
} from "@hcam/camera-live-domain";
import { generatedAdmissionRequests } from "@hcam/test-fixtures";

const mse = { mse: true, nativeHls: false, webrtc: true, codecs: ["avc1.42E01E"] } as const;
describe("media admission", () => {
  it.each([
    ["low_resource", 1],
    ["enhanced_workstation", 4],
    ["control_room", 10],
  ] as const)("applies the %s stream ceiling", (profile, count) => {
    const decisions = admitStreams(profile, generatedAdmissionRequests(), mse, false);
    expect(decisions.filter((decision) => decision.admitted)).toHaveLength(count);
    expect(decisions[0]!.streamId).toBe("SYN-STREAM-0001");
  });
  it("intersects decode network and server budgets", () => {
    const decisions = admitStreams("control_room", generatedAdmissionRequests(4), mse, false, {
      decodeUnits: 2,
      networkUnits: 2,
      serverUnits: 2,
    });
    expect(decisions.filter((decision) => decision.admitted).length).toBeLessThanOrEqual(2);
    expect(decisions.some((decision) => decision.reason === "profile_budget_exceeded")).toBe(true);
    for (const key of ["decodeUnits", "networkUnits", "serverUnits"] as const) {
      const budget = { decodeUnits: 100, networkUnits: 100, serverUnits: 100 };
      budget[key] = 0;
      expect(
        admitStreams("control_room", generatedAdmissionRequests(1), mse, false, budget)[0]
          ?.admitted,
      ).toBe(false);
    }
    const hidden = [{ ...generatedAdmissionRequests(1)[0]!, visible: false }];
    expect(admitStreams("control_room", hidden, mse)[0]?.reason).toBe("profile_budget_exceeded");
    const source = generatedAdmissionRequests(1)[0]!;
    const defaults = {
      streamId: source.streamId,
      priority: source.priority,
      requestedTransport: source.requestedTransport,
      requestedRendition: source.requestedRendition,
      visible: source.visible,
      focused: source.focused,
    };
    expect(admitStreams("control_room", [defaults], mse)[0]?.admitted).toBe(true);
    expect(
      admitStreams("control_room", [defaults], {
        mse: false,
        nativeHls: false,
        webrtc: false,
        codecs: [],
      })[0]?.reason,
    ).toBe("browser_unsupported");
  });
  it("chooses bounded transport fallback", () => {
    expect(selectTransport("whep", mse, true)).toBe("whep");
    expect(selectTransport("whep", mse, false)).toBe("hls");
    expect(
      selectTransport("hls", { mse: false, nativeHls: true, webrtc: false, codecs: [] }, false),
    ).toBe("native_hls");
    expect(
      selectTransport("hls", { mse: false, nativeHls: false, webrtc: false, codecs: [] }, false),
    ).toBe("none");
    expect(selectTransport("hls", mse, false)).toBe("hls");
  });
  it("uses deterministic bounded recovery", () => {
    expect(
      nextRecovery({ attempts: 0, firstFailureAt: 0, cooldownUntil: 0, circuitOpenUntil: 0 }, 1)
        .delayMs,
    ).toBe(1000);
    expect(
      nextRecovery({ attempts: 3, firstFailureAt: 0, cooldownUntil: 0, circuitOpenUntil: 0 }, 1)
        .reason,
    ).toBe("circuit_open");
    expect(
      nextRecovery({ attempts: 0, firstFailureAt: 0, cooldownUntil: 20, circuitOpenUntil: 0 }, 10)
        .reason,
    ).toBe("cooldown_active");
    expect(
      nextRecovery({ attempts: 0, firstFailureAt: 0, cooldownUntil: 0, circuitOpenUntil: 30 }, 10)
        .delayMs,
    ).toBe(20);
  });
  it("exposes invariant profile policy and sorted schedules", () => {
    expect(getResourceProfile("owned_gpu_lab").maxStreams).toBe(10);
    expect(clampRequestedStreams("low_resource", 9)).toBe(1);
    expect(clampRequestedStreams("low_resource", -1)).toBe(0);
    expect(clampRequestedStreams("low_resource", 1.5)).toBe(0);
    expect(clampRequestedStreams("control_room", 3)).toBe(3);
    const decisions = admitStreams("low_resource", generatedAdmissionRequests(2), mse);
    expect(scheduleAdmissions([...decisions].reverse())[0]!.admitted).toBe(true);
    expect(
      scheduleAdmissions([
        { ...decisions[0]!, admitted: true, rank: 2 },
        { ...decisions[0]!, admitted: true, rank: 1 },
      ])[0]?.rank,
    ).toBe(1);
    expect(
      nextRecovery({ attempts: -1, firstFailureAt: 0, cooldownUntil: 0, circuitOpenUntil: 0 }, 1),
    ).toEqual({ retry: false, delayMs: 60_000, reason: "circuit_open" });
  });
});
