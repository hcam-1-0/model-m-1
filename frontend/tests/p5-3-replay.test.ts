import { createHash } from "node:crypto";
import { describe, expect, it } from "vitest";
import { admitStreams } from "@hcam/camera-live-domain";
import { generatedAdmissionRequests, generatedCameras, generatedLayout } from "@hcam/test-fixtures";

function replay() {
  const output = {
    cameras: generatedCameras(),
    decisions: admitStreams(
      "control_room",
      generatedAdmissionRequests(),
      { mse: true, nativeHls: false, webrtc: true, codecs: ["avc1.42E01E"] },
      false,
    ),
    layout: generatedLayout(10),
  };
  return createHash("sha256").update(JSON.stringify(output)).digest("hex");
}
describe("P5.3 replay", () => {
  it("produces identical clean canonical outputs", () => expect(replay()).toBe(replay()));
});
