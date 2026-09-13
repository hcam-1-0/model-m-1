import { describe, expect, it } from "vitest";
import { classifyEvent, p55InvalidationBatch } from "@hcam/event-invalidation";
describe("P5.5 event invalidation", () => {
  const base = {
    eventType: "hcam.evidence.reference.changed.v1",
    version: "1.0.0",
    departmentRef: "SYN-DEPT-01",
    occurredAt: "2026-09-09T11:00:00Z",
    payload: {},
  };
  it("uses events as hints and requires HTTP confirmation", () => {
    expect(classifyEvent({ ...base, sequence: 2 }, "SYN-DEPT-01", 1)).toMatchObject({
      disposition: "accepted",
      revalidate: true,
    });
    expect(classifyEvent({ ...base, sequence: 5 }, "SYN-DEPT-01", 1).disposition).toBe("gap");
    expect(
      classifyEvent({ ...base, sequence: 2, departmentRef: "SYN-DEPT-02" }, "SYN-DEPT-01", 1)
        .revalidate,
    ).toBe(false);
    const batch = p55InvalidationBatch("correctionRecorded", 8);
    expect(batch.requiresHttpConfirmation).toBe(true);
    expect(batch.queryScopes).toContain("investigation.reconstruction");
  });
});
