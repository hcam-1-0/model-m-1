import { LayoutDashboard, MonitorUp } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router";
import { admitStreams, getResourceProfile, type ResourceProfileId } from "@hcam/camera-live-domain";
import { generatedAdmissionRequests } from "@hcam/test-fixtures";
import { AdmissionBudgetStrip } from "../components/admission-budget-strip";
import { LiveWorkspaceGrid } from "../components/live-workspace-grid";
import { WorkspaceToolbar } from "../components/workspace-toolbar";
import { cameras, generatedBrowserCapabilities } from "../data/camera-live-projections";

export function LiveWorkspacePage() {
  const [profileId, setProfileId] = useState<ResourceProfileId>("enhanced_workstation");
  const [columns, setColumns] = useState<1 | 2 | 3 | 4>(2);
  const decisions = useMemo(
    () =>
      admitStreams(profileId, generatedAdmissionRequests(), generatedBrowserCapabilities, false),
    [profileId],
  );
  const profile = getResourceProfile(profileId);
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">OPERATIONS / LIVE WORKSPACE</p>
          <h1>Live monitoring workspace</h1>
          <p>
            Deterministic generated stream admission with bounded quality, recovery, and teardown.
          </p>
        </div>
        <Link className="primary-link" to="/operations/wall">
          <MonitorUp size={16} /> Open monitor wall
        </Link>
      </header>
      <AdmissionBudgetStrip profile={profile} decisions={decisions} />
      <WorkspaceToolbar
        profile={profileId}
        columns={columns}
        onProfile={setProfileId}
        onColumns={setColumns}
        onReset={() => {
          setProfileId("enhanced_workstation");
          setColumns(2);
        }}
      />
      <LiveWorkspaceGrid cameras={cameras} decisions={decisions} columns={columns} />
      <div className="workspace-footnote">
        <LayoutDashboard size={16} />
        <span>
          Non-admitted tiles remain visible with authoritative status and can be promoted
          automatically when capacity becomes available.
        </span>
      </div>
    </>
  );
}
