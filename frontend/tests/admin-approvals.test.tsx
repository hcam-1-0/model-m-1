import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { evaluateSeparationOfDuty } from "../packages/governance-domain/src";
import { PolicyChangeRequestsPage } from "../apps/admin-center/src/pages/policy-change-requests-page";
describe("P5.6 independent approvals", () => {
  it("rejects self approval and renders chronology", () => {
    expect(
      evaluateSeparationOfDuty({
        requesterRef: "SYN-A",
        actorRef: "SYN-A",
        priorActorRefs: [],
        requiredApprovals: 2,
      }).reason,
    ).toBe("self_approval");
    render(
      <MemoryRouter>
        <PolicyChangeRequestsPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: "Policy and change requests" })).toBeInTheDocument();
    expect(screen.getAllByLabelText("Approval chronology").length).toBeGreaterThan(0);
  });
});
