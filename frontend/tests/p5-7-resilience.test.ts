import { describe, expect, it } from "vitest";
import { transitionRecovery } from "../packages/quality-domain/src";

describe("P5.7 bounded recovery", () => {
  it("requires authoritative refetch and reaches typed terminal states", () => {
    expect(transitionRecovery("healthy", "gap")).toBe("refetch_required");
    expect(transitionRecovery("refetch_required", "retry")).toBe("recovering");
    expect(transitionRecovery("recovering", "authoritative_success")).toBe("recovered");
    expect(transitionRecovery("recovering", "authoritative_failure")).toBe("terminal_failure");
    expect(transitionRecovery("degraded", "retry")).toBe("recovering");
    expect(transitionRecovery("terminal_failure", "reset")).toBe("healthy");
    expect(transitionRecovery("recovered", "retry")).toBe("degraded");
  });
});
