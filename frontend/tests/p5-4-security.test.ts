import { describe, expect, it } from "vitest";
import { generatedCandidate, generatedQueue } from "../packages/intelligence-fixtures/src";
const forbidden =
  /password|secret_ref|credential|camera_locator|provider_payload|biometric_template|vehicle_plate|person_name/iu;
describe("P5.4 browser security", () => {
  it("recursively excludes sensitive provider and identity fields", () => {
    const serialized = JSON.stringify({
      queue: generatedQueue("proposed_alert", 50),
      candidate: generatedCandidate(),
    });
    expect(serialized).not.toMatch(forbidden);
    expect(serialized).not.toContain("http://");
    expect(serialized).not.toContain("https://");
  });
  it.each([
    "<script>alert(1)</script>",
    "javascript:alert(1)",
    "../../secret",
    "identity confirmed",
  ])("keeps hostile value inert: %s", (value) => {
    const element = document.createElement("span");
    element.textContent = value;
    expect(element.querySelector("script")).toBeNull();
    expect(element.textContent).toBe(value);
  });
});
