import { describe, expect, it } from "vitest";
import {
  analyticalConceptKinds,
  generatedMarker,
  isIntelligenceEvent,
  safeIntelligenceProblem,
  canonicalQueryKey,
} from "../packages/intelligence-contracts/src";
import { generatedIntelligenceOperation } from "@hcam/api-client";
import { resolveReviewAuthority } from "@hcam/capabilities";
import { coalesceInvalidations } from "@hcam/event-invalidation";
import { validateIntelligenceSignal } from "@hcam/observability";
import { p54GeneratedPolicies } from "@hcam/query-policy";
describe("P5.4 intelligence contracts", () => {
  it("freezes eight separate analytical concepts", () => {
    expect(analyticalConceptKinds).toHaveLength(8);
    expect(new Set(analyticalConceptKinds).size).toBe(8);
    expect(generatedMarker).toContain("NON-OPERATIONAL");
  });
  it("accepts only bounded versioned events", () => {
    const event = {
      eventType: "hcam.intelligence.alert.changed.v1",
      version: "1.0.0",
      departmentRef: "SYN-DEPT-01",
      sequence: 1,
      occurredAt: "2026-09-09T09:00:00Z",
      payload: { resourceRef: "SYN-ALERT-0001", queryScopes: ["alerts"] },
    };
    expect(isIntelligenceEvent(event)).toBe(true);
    expect(isIntelligenceEvent(null)).toBe(false);
    expect(isIntelligenceEvent({ ...event, version: "2.0.0" })).toBe(false);
    expect(isIntelligenceEvent({ ...event, sequence: 1.2 })).toBe(false);
    expect(isIntelligenceEvent({ ...event, payload: null })).toBe(false);
    expect(isIntelligenceEvent({ ...event, payload: { resourceRef: 1, queryScopes: [] } })).toBe(
      false,
    );
    expect(
      isIntelligenceEvent({
        ...event,
        payload: { resourceRef: "SYN-A", queryScopes: Array(9).fill("x") },
      }),
    ).toBe(false);
  });
  it("uses safe problems and canonical department-scoped query keys", () => {
    expect(safeIntelligenceProblem("etag_mismatch")).toBe("etag_mismatch");
    expect(safeIntelligenceProblem("raw provider error")).toBe("producer_unavailable");
    expect(
      canonicalQueryKey({
        queue: "hypothesis",
        departmentRef: "SYN-DEPT-01",
        cursor: null,
        limit: 10,
      }),
    ).toEqual(["p5-4", "SYN-DEPT-01", "hypothesis", "first", "10", "all", "all"]);
  });
  it("binds same-origin operations and fail-closed authority", () => {
    const operation = generatedIntelligenceOperation(
      "generatedReview",
      "/api/intelligence/reviews",
      (value) => (typeof value === "string" ? value : null),
      true,
    );
    expect(operation).toMatchObject({
      method: "POST",
      requiresEtag: true,
      requiresIdempotency: true,
    });
    expect(() =>
      generatedIntelligenceOperation("unsafe", "/api/intelligence/x", () => null),
    ).toThrow();
    expect(() =>
      generatedIntelligenceOperation("generatedUnsafe", "/outside", () => null),
    ).toThrow();
    const base = {
      departmentMatches: true,
      policyCurrent: true,
      capabilities: ["intelligence.reviewer" as const],
      priorActorRefs: [],
      actorRef: "SYN-ACTOR",
    };
    expect(resolveReviewAuthority(base).allowed).toBe(true);
    expect(resolveReviewAuthority({ ...base, departmentMatches: false }).reason).toBe(
      "department_mismatch",
    );
    expect(resolveReviewAuthority({ ...base, policyCurrent: false }).reason).toBe("session_stale");
    expect(resolveReviewAuthority({ ...base, capabilities: [] }).reason).toBe("capability_missing");
    expect(resolveReviewAuthority({ ...base, priorActorRefs: ["SYN-ACTOR"] }).reason).toBe(
      "reauthentication_required",
    );
  });
  it("coalesces invalidation hints and validates low-cardinality signals", () => {
    expect(
      coalesceInvalidations(
        [
          { sequence: 2, queryScopes: ["alerts", "alerts", "bad scope"] },
          { sequence: 4, queryScopes: ["reviews"] },
        ],
        2,
      ),
    ).toEqual({
      queryScopes: ["alerts", "reviews"],
      highestSequence: 4,
      requiresHttpConfirmation: true,
    });
    expect(coalesceInvalidations([]).highestSequence).toBe(0);
    expect(
      validateIntelligenceSignal({
        name: "review_attempt",
        outcome: "conflict",
        reason: "conflict",
        profile: "low_resource",
        durationBucket: "lt500",
      }),
    ).toBe(true);
    expect(
      validateIntelligenceSignal({
        name: "review_attempt",
        outcome: "conflict",
        reason: "raw provider 10.0.0.1" as never,
        profile: "low_resource",
        durationBucket: "lt500",
      }),
    ).toBe(false);
    expect(p54GeneratedPolicies.reviewCommand.retryLimit).toBe(0);
  });
});
