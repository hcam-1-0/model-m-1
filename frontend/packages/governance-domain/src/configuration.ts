export type ConfigurationKind =
  "feature_flag" | "runtime_profile" | "model_lane" | "deployment_profile" | "kill_switch";
export interface ConfigurationProposal {
  readonly ref: string;
  readonly kind: ConfigurationKind;
  readonly currentValue: string;
  readonly proposedValue: string;
  readonly impact: readonly string[];
  readonly approvalRequired: true;
  readonly activationAvailable: false;
  readonly generated: true;
}
export function makeConfigurationProposal(
  ref: string,
  kind: ConfigurationKind,
  currentValue: string,
  proposedValue: string,
): ConfigurationProposal {
  return {
    ref,
    kind,
    currentValue,
    proposedValue,
    impact: ["Generated impact preview only", "No runtime setting changes"],
    approvalRequired: true,
    activationAvailable: false,
    generated: true,
  };
}
