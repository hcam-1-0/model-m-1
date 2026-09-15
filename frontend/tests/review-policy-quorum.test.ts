import { describe, expect, it } from "vitest";
import { evaluateReviewPolicy, projectQuorum } from "../packages/review-workflows/src";
import { generatedReviewPolicy, generatedReviews } from "../packages/intelligence-fixtures/src";
describe("P5.4 server-authoritative review policy", () => {
  const reviews = generatedReviews();
  it("denies stale policy, forbidden role, duplicate actor, and outcome override", () => {
    expect(
      evaluateReviewPolicy(
        generatedReviewPolicy,
        "old",
        ["intelligence.reviewer"],
        "SYN-BETA",
        reviews,
        "abstain",
      ),
    ).toBe("stale_policy");
    expect(
      evaluateReviewPolicy(
        generatedReviewPolicy,
        generatedReviewPolicy.policyRevision,
        [],
        "SYN-BETA",
        reviews,
        "abstain",
      ),
    ).toBe("forbidden_role");
    expect(
      evaluateReviewPolicy(
        generatedReviewPolicy,
        generatedReviewPolicy.policyRevision,
        ["intelligence.reviewer"],
        "SYN-ACTOR-ALPHA",
        reviews,
        "abstain",
      ),
    ).toBe("duplicate_actor");
    expect(
      evaluateReviewPolicy(
        { ...generatedReviewPolicy, allowedOutcomes: ["reject"] },
        generatedReviewPolicy.policyRevision,
        ["intelligence.reviewer"],
        "SYN-BETA",
        reviews,
        "abstain",
      ),
    ).toBe("outcome_denied");
    expect(
      evaluateReviewPolicy(
        generatedReviewPolicy,
        generatedReviewPolicy.policyRevision,
        ["intelligence.reviewer"],
        "SYN-BETA",
        reviews,
        "abstain",
      ),
    ).toBe("allowed");
  });
  it("requires independent approvals", () => {
    expect(projectQuorum(generatedReviewPolicy, reviews)).toMatchObject({
      reached: false,
      approvals: 1,
      required: 2,
      serverAuthoritative: true,
    });
    const second = {
      ...reviews[0]!,
      reviewRef: "SYN-REVIEW-0002" as (typeof reviews)[0]["reviewRef"],
      actorRef: "SYN-ACTOR-BETA",
    };
    expect(projectQuorum(generatedReviewPolicy, [...reviews, second]).reached).toBe(true);
    expect(
      projectQuorum(generatedReviewPolicy, [...reviews, { ...second, actorRef: "SYN-ACTOR-ALPHA" }])
        .reached,
    ).toBe(false);
  });
});
