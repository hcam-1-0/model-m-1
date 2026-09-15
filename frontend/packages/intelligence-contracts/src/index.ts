export * from "./contracts";
export * from "./events";
export * from "./problems";
export * from "./queries";

export interface InvestigationHandoffProjection {
  readonly hypothesisRef: string;
  readonly proposedAlertRef: string;
  readonly investigationRef: string;
  readonly reviewRecorded: true;
  readonly operationalActionAuthorized: false;
  readonly generated: true;
}
