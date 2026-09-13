import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AccessAssuranceMatrix } from "../apps/security-center/src/components/access-assurance-matrix";
import { CapabilityMatrix } from "../apps/admin-center/src/components/capability-matrix";
describe("P5.6 authoritative accessibility alternatives", () => {
  it("provides real tables for core projections", () => {
    render(
      <>
        <CapabilityMatrix />
        <AccessAssuranceMatrix />
      </>,
    );
    expect(screen.getAllByRole("table")).toHaveLength(2);
    expect(screen.getAllByRole("columnheader").length).toBeGreaterThan(6);
  });
});
