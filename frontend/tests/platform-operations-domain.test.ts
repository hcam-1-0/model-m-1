import { describe, expect, it } from "vitest";
import {
  aggregateServiceState,
  generatedSloBoundary,
  operationsState,
  queueDisposition,
  recoveryControls,
  supplyChainBoundary,
} from "../packages/platform-operations-domain/src";
import {
  generatedQueues,
  generatedServices,
} from "../packages/admin-security-operations-fixtures/src";
describe("P5.6 platform operations domain", () => {
  it("aggregates qualified state conservatively", () => {
    expect(aggregateServiceState([])).toBe("unknown");
    expect(aggregateServiceState(generatedServices(12))).not.toBe("healthy");
  });
  it("fails queues closed", () => {
    const queue = generatedQueues(1)[0]!;
    expect(queueDisposition(queue)).toBe("fail_closed");
  });
  it("keeps execution surfaces closed", () => {
    expect(generatedSloBoundary.productionTarget).toBe(false);
    expect(recoveryControls).toEqual({
      backup: false,
      restore: false,
      failover: false,
      maintenance: false,
      disasterRecovery: false,
    });
    expect(supplyChainBoundary).toEqual({
      scannerExecution: false,
      artifactAcquisition: false,
      attestationSigning: false,
      mutation: false,
    });
    expect(
      operationsState({
        authorized: true,
        loading: false,
        itemCount: 1,
        stale: false,
        complete: true,
        recovering: false,
        failed: false,
      }),
    ).toBe("ready");
  });
});
