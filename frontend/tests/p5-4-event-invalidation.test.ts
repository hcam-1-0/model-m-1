import { describe, expect, it } from "vitest";
import { classifyEvent } from "@hcam/event-invalidation";
describe("P5.4 event invalidation", () => {
  const base = {
    eventType: "hcam.intelligence.queue.changed.v1",
    version: "1.0.0" as const,
    departmentRef: "SYN-DEPT-01",
    occurredAt: "2026-09-09T09:00:00Z",
    payload: {},
  };
  it("treats events only as scoped revalidation hints", () => {
    expect(classifyEvent({ ...base, sequence: 2 }, "SYN-DEPT-01", 1)).toEqual({
      disposition: "accepted",
      revalidate: true,
      nextSequence: 2,
    });
    expect(classifyEvent({ ...base, sequence: 1 }, "SYN-DEPT-01", 1).revalidate).toBe(false);
    expect(classifyEvent({ ...base, sequence: 5 }, "SYN-DEPT-01", 1).disposition).toBe("gap");
    expect(classifyEvent({ ...base, sequence: 0 }, "SYN-DEPT-01", 1).disposition).toBe("reordered");
    expect(
      classifyEvent({ ...base, sequence: 2, departmentRef: "SYN-DEPT-02" }, "SYN-DEPT-01", 1)
        .revalidate,
    ).toBe(false);
    expect(
      classifyEvent({ ...base, version: "9.0.0", sequence: 2 }, "SYN-DEPT-01", 1).disposition,
    ).toBe("unknown_version");
  });
});
