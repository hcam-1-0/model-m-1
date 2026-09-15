import { ArrowLeft, MonitorUp } from "lucide-react";
import { Link } from "react-router";
import { admissions, cameras } from "../data/camera-live-projections";
import { MonitorWall } from "../components/monitor-wall";

export function MonitorWallPage() {
  const decisions = admissions("control_room");
  return (
    <div className="wall-page">
      <header className="wall-toolbar">
        <Link to="/operations/live">
          <ArrowLeft size={16} /> Live workspace
        </Link>
        <div>
          <MonitorUp size={16} />
          <strong>Generated monitor wall</strong>
        </div>
        <span>CONTROL ROOM PROFILE · VIEW ONLY</span>
      </header>
      <MonitorWall cameras={cameras} decisions={decisions} />
    </div>
  );
}
