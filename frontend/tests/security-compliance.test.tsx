import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PoliciesExceptionsAttestationsPage } from "../apps/security-center/src/pages/policies-exceptions-attestations-page";
describe("P5.6 compliance projections", () => {
  it("does not permit attestation signing", () => {
    render(<PoliciesExceptionsAttestationsPage />);
    expect(screen.getByRole("button", { name: "Sign attestation" })).toBeDisabled();
    expect(screen.getByText("Legal decision")).toBeInTheDocument();
  });
});
