import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AuditReferenceExplorerPage } from "../apps/security-center/src/pages/audit-reference-explorer-page";
describe("P5.6 audit lane", () => {
  it("renders immutable references separately", () => {
    render(<AuditReferenceExplorerPage />);
    expect(screen.getByRole("heading", { name: "Audit reference explorer" })).toBeInTheDocument();
    expect(screen.getAllByText("immutable reference").length).toBeGreaterThan(0);
  });
});
