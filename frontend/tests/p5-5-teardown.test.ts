import { describe, expect, it } from "vitest";
import { disabledSignalAdapter } from "@hcam/observability";
import { p55GeneratedPolicies } from "@hcam/query-policy";
describe("P5.5 teardown and recovery", () => {
  it("keeps telemetry disabled and mutations non-retrying", () => {
    expect(() =>
      disabledSignalAdapter.emit({
        name: "source_boundary",
        portal: "evidence",
        routeClass: "detail",
        state: "ready",
        outcome: "ok",
        durationBucket: "lt100",
      }),
    ).not.toThrow();
    expect(() => disabledSignalAdapter.shutdown()).not.toThrow();
    expect(disabledSignalAdapter.enabled).toBe(false);
    expect(p55GeneratedPolicies.conflictCommand.retryLimit).toBe(0);
    expect(p55GeneratedPolicies.conflictCommand.persist).toBe(false);
  });
});
