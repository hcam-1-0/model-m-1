import { describe, expect, it } from "vitest";
import {
  administrationGeneratedMarker,
  adminQueryKey,
  isAdminCatalogue,
  isAdminInvalidationEvent,
  safeAdminProblem,
} from "../packages/admin-contracts/src";
import { generatedAdminResources } from "../packages/admin-security-operations-fixtures/src";
describe("P5.6 administration contracts", () => {
  it("accepts bounded generated catalogues", () => {
    const catalogue = {
      contractVersion: "1.0.0",
      marker: administrationGeneratedMarker,
      items: generatedAdminResources(5),
      nextCursor: null,
      authoritativeOrder: "server_sequence_then_ref",
    };
    expect(isAdminCatalogue(catalogue)).toBe(true);
    expect(isAdminCatalogue({ ...catalogue, unexpected: true })).toBe(false);
    expect(isAdminCatalogue({ ...catalogue, items: [{ ref: "REAL", generated: false }] })).toBe(
      false,
    );
  });
  it("uses canonical scoped keys and safe failures", () => {
    expect(
      adminQueryKey({
        departmentRef: "SYN-DEPT-01",
        resource: "role",
        state: "all",
        cursor: null,
        limit: 25,
      }),
    ).toEqual(["p5-6", "admin", "SYN-DEPT-01", "role", "all", "first", "25"]);
    expect(safeAdminProblem("raw stack")).toBe("safe_failure");
  });
  it("rejects invalid invalidation events", () => {
    expect(
      isAdminInvalidationEvent({
        eventType: "hcam.admin.projection.changed.v1",
        version: "1.0.0",
        departmentRef: "SYN-DEPT-01",
        sequence: 1,
        queryScopes: ["admin.roles"],
        generated: true,
      }),
    ).toBe(true);
    expect(isAdminInvalidationEvent({ eventType: "wrong", generated: true })).toBe(false);
  });
});
