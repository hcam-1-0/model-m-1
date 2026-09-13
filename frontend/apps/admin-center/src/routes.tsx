import { Route, Routes } from "react-router";
import { AdminOverviewPage } from "./pages/admin-overview-page";
import { CameraStreamGovernancePage } from "./pages/camera-stream-governance-page";
import { FeaturesConfigurationPage } from "./pages/features-configuration-page";
import { IntegrationProviderGovernancePage } from "./pages/integration-provider-governance-page";
import { OrganizationsDepartmentsPage } from "./pages/organizations-departments-page";
import { PolicyChangeRequestsPage } from "./pages/policy-change-requests-page";
import { ResourceModelDeploymentProfilesPage } from "./pages/resource-model-deployment-profiles-page";
import { RetentionPolicyProjectionsPage } from "./pages/retention-policy-projections-page";
import { RolesPermissionsSodPage } from "./pages/roles-permissions-sod-page";
import { UsersMembershipsSessionsPage } from "./pages/users-memberships-sessions-page";
export const adminRoutes = [
  ["/admin", "Overview"],
  ["/admin/organizations", "Organizations"],
  ["/admin/identities", "Users and sessions"],
  ["/admin/roles", "Roles and permissions"],
  ["/admin/changes", "Change requests"],
  ["/admin/cameras", "Camera governance"],
  ["/admin/providers", "Provider governance"],
  ["/admin/configuration", "Features and configuration"],
  ["/admin/profiles", "Resource profiles"],
  ["/admin/retention", "Retention projections"],
] as const;
export function AdminRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AdminOverviewPage />} />
      <Route path="/admin" element={<AdminOverviewPage />} />
      <Route path="/admin/organizations" element={<OrganizationsDepartmentsPage />} />
      <Route path="/admin/identities" element={<UsersMembershipsSessionsPage />} />
      <Route path="/admin/roles" element={<RolesPermissionsSodPage />} />
      <Route path="/admin/changes" element={<PolicyChangeRequestsPage />} />
      <Route path="/admin/cameras" element={<CameraStreamGovernancePage />} />
      <Route path="/admin/providers" element={<IntegrationProviderGovernancePage />} />
      <Route path="/admin/configuration" element={<FeaturesConfigurationPage />} />
      <Route path="/admin/profiles" element={<ResourceModelDeploymentProfilesPage />} />
      <Route path="/admin/retention" element={<RetentionPolicyProjectionsPage />} />
      <Route path="*" element={<AdminOverviewPage />} />
    </Routes>
  );
}
