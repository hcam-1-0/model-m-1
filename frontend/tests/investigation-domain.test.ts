import { describe, expect, it } from "vitest";
import {
  compareRevisions,
  chronologyHasUncertainty,
  decodeStableCursor,
  encodeStableCursor,
  evidenceReferenceState,
  eventContextChronology,
  investigationQueueState,
  limitsForInvestigationProfile,
  recordChronology,
  reconstructionSequenceIsBounded,
  stablePage,
  timelineState,
  validateReconstruction,
} from "../packages/investigation-domain/src";
import {
  generatedEvidenceReferences,
  generatedInvestigationQueue,
  generatedInvestigations,
  generatedReconstruction,
  generatedTimeline,
  generatedTimelinePage,
} from "../packages/investigation-fixtures/src";

describe("P5.5 investigation domain", () => {
  it("keeps record sequence authoritative", () => {
    const reversed = [...generatedTimeline(1, 20)].reverse();
    expect(recordChronology(reversed).entries[0]?.recordSequence).toBe(1);
    expect(eventContextChronology(reversed)).toMatchObject({
      authority: "record_sequence",
      qualified: true,
    });
    expect(chronologyHasUncertainty(reversed)).toBe(true);
  });
  it("uses stable bounded pagination", () => {
    const items = generatedInvestigations(50);
    const page = stablePage(items, encodeStableCursor(10), 10);
    expect(page.items).toHaveLength(10);
    expect(page.nextCursor).toBe("SYN-P55-CURSOR-20");
    expect(decodeStableCursor(null)).toBe(0);
    expect(() => decodeStableCursor("../10")).toThrow();
    expect(() => encodeStableCursor(-1)).toThrow();
    expect(() => encodeStableCursor(Number.NaN)).toThrow();
    expect(() => encodeStableCursor(100_001)).toThrow();
    expect(stablePage(items, "SYN-P55-CURSOR-40", 10).nextCursor).toBeNull();
  });
  it("validates exact revision reconstruction and comparison", () => {
    const before = generatedReconstruction(7, "partial");
    const after = generatedReconstruction(8, "complete");
    expect(validateReconstruction(before)).toEqual([]);
    expect(compareRevisions(before, after)).toMatchObject({
      fromRevision: "SYN-REV-0007",
      toRevision: "SYN-REV-0008",
      complete: false,
    });
    expect(() =>
      compareRevisions(before, { ...after, investigationRef: "SYN-OTHER" as never }),
    ).toThrow();
  });
  it("covers exact-revision rejection and sequence ceilings", () => {
    const valid = generatedReconstruction(7, "complete");
    const invalid = {
      ...valid,
      requestedRevision: "bad",
      resolvedRevision: "SYN-REV-0008",
      digest: "bad",
      completeness: "partial" as const,
      omittedComponents: ["source"],
      limitations: [],
      generated: false,
    } as unknown as typeof valid;
    expect(validateReconstruction(invalid)).toEqual([
      "invalid_requested_revision",
      "revision_not_exact",
      "invalid_digest",
      "missing_incompleteness_limitation",
      "omission_without_limitation",
      "not_generated",
    ]);
    expect(reconstructionSequenceIsBounded(valid)).toBe(true);
    expect(
      reconstructionSequenceIsBounded({
        ...valid,
        timeline: valid.timeline.map((entry, index) =>
          index === 0 ? { ...entry, revisionRef: "SYN-REV-9999" } : entry,
        ),
      }),
    ).toBe(false);
    expect(
      reconstructionSequenceIsBounded({
        ...valid,
        timeline: Array.from({ length: 201 }, () => valid.timeline[0]!),
      }),
    ).toBe(false);
  });
  it("classifies every investigation, timeline, and evidence state", () => {
    const now = new Date("2026-09-09T11:00:00.000Z");
    const queue = generatedInvestigationQueue(3);
    const cleanItems = queue.items.map((item) => ({
      ...item,
      correctionStatus: "clear" as const,
      freshness: { ...item.freshness, completeness: "complete" as const },
    }));
    expect(investigationQueueState(null, now)).toBe("loading");
    expect(investigationQueueState({ ...queue, items: [] }, now)).toBe("empty");
    expect(investigationQueueState(queue, now)).toBe("correction");
    expect(
      investigationQueueState(
        {
          ...queue,
          items: cleanItems.map((item) => ({
            ...item,
            freshness: { ...item.freshness, staleAt: "2026-09-09T10:00:00.000Z" },
          })),
        },
        now,
      ),
    ).toBe("stale");
    expect(
      investigationQueueState(
        {
          ...queue,
          items: cleanItems.map((item, index) => ({
            ...item,
            freshness: {
              ...item.freshness,
              completeness: index === 0 ? ("partial" as const) : ("complete" as const),
              staleAt: "2026-09-09T12:00:00.000Z",
            },
          })),
        },
        now,
      ),
    ).toBe("partial");
    expect(
      investigationQueueState(
        {
          ...queue,
          items: cleanItems.map((item) => ({
            ...item,
            freshness: { ...item.freshness, staleAt: "2026-09-09T12:00:00.000Z" },
          })),
        },
        now,
      ),
    ).toBe("ready");

    const page = generatedTimelinePage(3);
    const baseEntry = { ...page.items[0]!, kind: "observation" as const, limitations: [] };
    expect(timelineState(null)).toBe("loading");
    expect(timelineState({ ...page, items: [] })).toBe("empty");
    expect(timelineState({ ...page, items: [{ ...baseEntry, kind: "retraction" }] })).toBe(
      "retracted",
    );
    expect(timelineState({ ...page, items: [{ ...baseEntry, limitations: ["partial"] }] })).toBe(
      "partial",
    );
    expect(timelineState({ ...page, items: [baseEntry] })).toBe("ready");

    const evidence = generatedEvidenceReferences(2)[1]!;
    const ready = {
      ...evidence,
      access: "allowed" as const,
      availability: "referenced" as const,
      integrity: "digest_observed" as const,
      freshness: { ...evidence.freshness, completeness: "complete" as const },
    };
    expect(evidenceReferenceState(null)).toBe("loading");
    expect(evidenceReferenceState({ ...ready, access: "denied" })).toBe("denied");
    expect(evidenceReferenceState({ ...ready, availability: "unavailable" })).toBe("degraded");
    expect(evidenceReferenceState({ ...ready, integrity: "digest_mismatch" })).toBe("conflict");
    expect(
      evidenceReferenceState({
        ...ready,
        freshness: { ...ready.freshness, completeness: "partial" },
      }),
    ).toBe("partial");
    expect(evidenceReferenceState(ready)).toBe("ready");
  });
  it("preserves authority across every presentation profile", () => {
    for (const profile of [
      "low_resource",
      "enhanced_workstation",
      "control_room",
      "owned_gpu_lab",
      "future_server",
    ] as const) {
      expect(limitsForInvestigationProfile(profile)).toMatchObject({
        authorityChanged: false,
        semanticsChanged: false,
      });
    }
  });
});
