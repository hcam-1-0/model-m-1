import {
  generatedAdminResources,
  generatedChangeRequests,
  generatedProviderPosture,
} from "../../../../packages/admin-security-operations-fixtures/src";
import {
  governanceProfiles,
  governanceProfile,
  makeConfigurationProposal,
  retentionPreview,
} from "../../../../packages/governance-domain/src";
export const adminResources = generatedAdminResources(36);
export const changeRequests = generatedChangeRequests(14);
export const providerPosture = generatedProviderPosture(8);
export const profileProjections = governanceProfiles.map(governanceProfile);
export const configurationProposals = [
  makeConfigurationProposal("SYN-CONFIG-0001", "feature_flag", "disabled", "review_requested"),
  makeConfigurationProposal(
    "SYN-CONFIG-0002",
    "runtime_profile",
    "low_resource",
    "enhanced_workstation",
  ),
  makeConfigurationProposal("SYN-CONFIG-0003", "model_lane", "disabled", "generated_preview"),
  makeConfigurationProposal(
    "SYN-CONFIG-0004",
    "deployment_profile",
    "standalone",
    "future_Kubernetes",
  ),
  makeConfigurationProposal("SYN-CONFIG-0005", "kill_switch", "declared", "review_requested"),
];
export const retentionProjections = Array.from({ length: 6 }, (_, index) =>
  retentionPreview(index + 1),
);
export const adminSummary = Object.freeze({
  organizations: 5,
  departments: 50,
  identities: 500,
  openChanges: changeRequests.filter((item) =>
    ["submitted", "independent_review"].includes(item.status),
  ).length,
  producerGaps: 48,
  generated: true,
} as const);
