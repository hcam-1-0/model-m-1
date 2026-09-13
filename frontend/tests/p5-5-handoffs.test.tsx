import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { EvidenceHandoff } from "../apps/investigation-center/src/components/evidence-handoff";
import { authorizeEvidenceReference } from "../packages/evidence-domain/src";
import {
  generatedEvidenceHandoff,
  generatedEvidenceReferences,
} from "../packages/investigation-fixtures/src";
afterEach(cleanup);
describe("P5.5 handoffs", () => {
  it("binds reference, investigation, department, purpose, and capability", () => {
    const reference = generatedEvidenceReferences(1)[0]!;
    const handoff = generatedEvidenceHandoff(1);
    const context = {
      departmentRef: handoff.departmentRef,
      purposeCode: handoff.purposeCode,
      capabilities: [handoff.capability],
      investigationRef: handoff.investigationRef,
    };
    expect(authorizeEvidenceReference(reference, handoff, context)).toBe(true);
    expect(
      authorizeEvidenceReference(reference, handoff, { ...context, departmentRef: "SYN-DEPT-02" }),
    ).toBe(false);
    render(<EvidenceHandoff reference={reference} />);
    expect(screen.getByText("Source unresolved")).toBeVisible();
    expect(
      screen.getByRole("link", { name: /independently authorized Evidence Desk/i }),
    ).toHaveAttribute("href", expect.stringContaining("/evidence/"));
  });
});
