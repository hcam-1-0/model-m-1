import { describe, expect, it } from "vitest";
import { generatedInvestigationOperation } from "@hcam/api-client";
import { resolveInvestigationEvidenceAuthority } from "@hcam/capabilities";
import {
  generatedContractCases,
  generatedInvestigationQueue,
} from "../packages/investigation-fixtures/src";
import {
  investigationQueryKey,
  isInvestigationEvent,
  safeInvestigationProblem,
  timelineKinds,
} from "../packages/investigation-contracts/src";

describe("P5.5 investigation contracts", () => {
  it("materializes the exact bounded contract inventory", () => {
    expect(timelineKinds).toHaveLength(11);
    expect(new Set(timelineKinds).size).toBe(11);
    expect(generatedContractCases).toHaveLength(960);
    expect(generatedInvestigationQueue(50).items).toHaveLength(50);
  });
  it("accepts only versioned HTTP-confirmed events", () => {
    const event = {
      eventType: "hcam.investigation.timeline.changed.v1",
      version: "1.0.0",
      departmentRef: "SYN-DEPT-01",
      sequence: 4,
      occurredAt: "2026-09-09T11:00:00Z",
      payload: {
        resourceRef: "SYN-TIMELINE-0001",
        investigationRef: "SYN-INVESTIGATION-0001",
        queryScopes: ["investigation.timeline"],
        requiresHttpConfirmation: true,
      },
    };
    expect(isInvestigationEvent(event)).toBe(true);
    expect(isInvestigationEvent({ ...event, version: "2.0.0" })).toBe(false);
    expect(
      isInvestigationEvent({
        ...event,
        payload: { ...event.payload, requiresHttpConfirmation: false },
      }),
    ).toBe(false);
    expect(isInvestigationEvent(null)).toBe(false);
  });
  it("binds same-origin paths, query identity, safe problems, and access", () => {
    const operation = generatedInvestigationOperation(
      "generatedTimeline",
      "/api/investigations/SYN-1/timeline",
      (value) => value,
      false,
    );
    expect(operation).toMatchObject({ method: "GET", command: false, requiresEtag: false });
    expect(() =>
      generatedInvestigationOperation("unsafe", "/api/investigations/x", () => null),
    ).toThrow();
    expect(() =>
      generatedInvestigationOperation("generatedUnsafe", "/outside", () => null),
    ).toThrow();
    expect(
      investigationQueryKey({
        departmentRef: "SYN-DEPT-01",
        purposeCode: "SYN-PURPOSE",
        cursor: null,
        limit: 10,
        chronology: "record",
      }),
    ).toEqual(["p5-5", "SYN-DEPT-01", "SYN-PURPOSE", "first", "10", "all", "all", "record"]);
    expect(safeInvestigationProblem("etag_mismatch")).toBe("etag_mismatch");
    expect(safeInvestigationProblem("raw secret")).toBe("producer_unavailable");
    expect(
      resolveInvestigationEvidenceAuthority({
        departmentMatches: true,
        purposeMatches: true,
        policyCurrent: true,
        capability: "evidence.viewer",
        capabilities: ["evidence.viewer"],
      }).allowed,
    ).toBe(true);
    expect(
      resolveInvestigationEvidenceAuthority({
        departmentMatches: true,
        purposeMatches: false,
        policyCurrent: true,
        capability: "evidence.viewer",
        capabilities: ["evidence.viewer"],
      }).allowed,
    ).toBe(false);
  });
});
