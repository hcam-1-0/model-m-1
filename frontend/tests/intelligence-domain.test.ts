import { describe, expect, it } from "vitest";
import {
  assertSafeAnalyticalCopy,
  canTransitionAlert,
  filterQueue,
  intelligenceQueueState,
  isAnalyticalConceptKind,
  isCommandReceipt,
  limitsForIntelligenceProfile,
  presentationFor,
  reviewReasonLabel,
  transitionAlert,
} from "../packages/intelligence-domain/src";
import { generatedAlert, generatedQueue } from "../packages/intelligence-fixtures/src";
describe("P5.4 semantic and lifecycle domain", () => {
  it("keeps analytical kinds and copy non-accusatory", () => {
    expect(isAnalyticalConceptKind("candidate")).toBe(true);
    expect(isAnalyticalConceptKind("identity")).toBe(false);
    expect(presentationFor("candidate").caution).toBe("Identity is not established");
    expect(assertSafeAnalyticalCopy("Generated candidate comparison")).toContain("candidate");
    expect(() => assertSafeAnalyticalCopy("identity confirmed")).toThrow(
      "forbidden_analytical_claim",
    );
    expect(() => assertSafeAnalyticalCopy("")).toThrow();
    expect(() => assertSafeAnalyticalCopy("x".repeat(241))).toThrow();
  });
  it("allows only explicit lifecycle transitions", () => {
    const alert = generatedAlert();
    expect(canTransitionAlert("proposed", "in_review")).toBe(true);
    expect(canTransitionAlert("retracted", "proposed")).toBe(false);
    expect(transitionAlert(alert, "in_review")).toMatchObject({
      lifecycle: "in_review",
      revision: 2,
    });
    expect(() => transitionAlert({ ...alert, lifecycle: "retracted" }, "proposed")).toThrow(
      "invalid_lifecycle_transition",
    );
  });
  it("projects loading, empty, correction, stale, partial, and ready states", () => {
    const now = new Date("2026-09-09T09:45:00Z");
    const queue = generatedQueue("hypothesis", 3);
    expect(intelligenceQueueState(null, now)).toBe("loading");
    expect(intelligenceQueueState({ ...queue, items: [] }, now)).toBe("empty");
    expect(intelligenceQueueState(queue, now)).toBe("correction");
    expect(
      intelligenceQueueState(
        {
          ...queue,
          items: queue.items.map((item) => ({
            ...item,
            state: "ready",
            freshness: { ...item.freshness, staleAt: "2026-09-09T09:00:00Z" },
          })),
        },
        now,
      ),
    ).toBe("stale");
    expect(
      intelligenceQueueState(
        {
          ...queue,
          items: [
            {
              ...queue.items[1]!,
              state: "ready",
              freshness: { ...queue.items[1]!.freshness, completeness: "partial" },
            },
          ],
        },
        now,
      ),
    ).toBe("partial");
    expect(
      intelligenceQueueState({ ...queue, items: [{ ...queue.items[1]!, state: "ready" }] }, now),
    ).toBe("ready");
  });
  it("filters queue state and priority independently", () => {
    const items = generatedQueue("hypothesis", 8).items;
    expect(filterQueue(items, "all", "all")).toHaveLength(8);
    expect(filterQueue(items, "correction_pending", "all")).toHaveLength(2);
    expect(filterQueue(items, "all", "urgent_review")).toHaveLength(2);
    expect(filterQueue(items, "awaiting_review", "standard_review")).toHaveLength(2);
  });
  it("recognizes immutable receipts and safe reason labels", () => {
    const receipt = {
      receiptRef: "SYN-RECEIPT-0001",
      commandFingerprint: "A".repeat(64),
      resultingRevision: 2,
      resultingEtag: '"SYN-ETAG-2"',
      recordedAt: "2026-09-09T09:00:00Z",
      replayed: false,
      externalSideEffects: false,
    };
    expect(isCommandReceipt(receipt)).toBe(true);
    expect(isCommandReceipt(null)).toBe(false);
    expect(isCommandReceipt({ ...receipt, receiptRef: 1 })).toBe(false);
    expect(isCommandReceipt({ ...receipt, commandFingerprint: "bad" })).toBe(false);
    expect(isCommandReceipt({ ...receipt, externalSideEffects: true })).toBe(false);
    expect(isCommandReceipt({ ...receipt, resultingRevision: 1.5 })).toBe(false);
    expect(reviewReasonLabel("evidence_sufficient")).toContain("sufficient");
    expect(reviewReasonLabel("not_allowlisted")).toBe("Reason unavailable");
    expect(limitsForIntelligenceProfile("control_room").authorityChanged).toBe(false);
  });
});
