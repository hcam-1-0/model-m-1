import {
  generatedDegradation,
  generatedQueues,
  generatedRecoveryPreviews,
  generatedServices,
  generatedSlos,
  generatedSupplyChain,
  generatedTopologies,
  p56Workloads,
  workloadTotals,
} from "../../../../packages/admin-security-operations-fixtures/src";
import {
  aggregateServiceState,
  operationsProfiles,
  operationsProfilePresentation,
  queueDisposition,
  supplyChainAttention,
} from "../../../../packages/platform-operations-domain/src";
export const platformServices = generatedServices(20);
export const platformQueues = generatedQueues(16);
export const platformSlos = generatedSlos(8);
export const platformDegradation = generatedDegradation;
export const recoveryPreviews = generatedRecoveryPreviews();
export const topologyProjections = generatedTopologies();
export const supplyChain = generatedSupplyChain(10);
export const platformSummary = Object.freeze({
  state: aggregateServiceState(platformServices),
  services: platformServices.length,
  queues: platformQueues.length,
  queuesNeedingAttention: platformQueues.filter((item) => queueDisposition(item) !== "normal")
    .length,
  supplyChainAttention: supplyChain.filter((item) => supplyChainAttention(item).length > 0).length,
  generated: true,
} as const);
export const capacityEvidence = (["C1", "C10", "C50"] as const).map(workloadTotals);
export const platformProfileProjections = operationsProfiles.map(operationsProfilePresentation);
export { p56Workloads };
