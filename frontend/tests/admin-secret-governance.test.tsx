import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  containsProhibitedSecretField,
  sanitizeProjection,
} from "../packages/governance-domain/src";
import { SecretReferencePanel } from "../apps/admin-center/src/components/secret-reference-panel";
describe("P5.6 secret governance", () => {
  it("removes prohibited fields and blocks nested values", () => {
    expect(sanitizeProjection({ label: "safe", password: "bad" })).toEqual({ label: "safe" });
    expect(containsProhibitedSecretField({ nested: { access_token: "bad" } })).toBe(true);
  });
  it("renders only an opaque reference and unavailable control", () => {
    render(<SecretReferencePanel />);
    expect(screen.getByText("SYN-SECRET-REF-PROVIDER-01")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reveal secret" })).toBeDisabled();
  });
});
