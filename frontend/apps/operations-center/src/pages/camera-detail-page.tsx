import { ArrowLeft, MapPin, RadioTower } from "lucide-react";
import { Link, useParams } from "react-router";
import { CameraHealthBadge } from "../components/camera-health-badge";
import { CapabilitySummary } from "../components/capability-summary";
import { DiagnosticsTimeline } from "../components/diagnostics-timeline";
import { StateBoundary } from "../components/state-boundary";
import { cameraById } from "../data/camera-live-projections";

export function CameraDetailPage() {
  const { cameraId } = useParams();
  const camera = cameraById(cameraId);
  if (!camera)
    return (
      <StateBoundary state="empty">
        <span />
      </StateBoundary>
    );
  const stream = camera.streams[0];
  if (!stream)
    return (
      <StateBoundary state="partial">
        <span />
      </StateBoundary>
    );
  return (
    <>
      <header className="page-heading">
        <div>
          <Link className="back-link" to="/operations/cameras">
            <ArrowLeft size={15} /> Camera catalogue
          </Link>
          <p className="eyebrow">CAMERA DETAIL / GENERATED</p>
          <h1>{camera.label}</h1>
          <p>
            <MapPin size={14} /> {camera.shortLocation}, {camera.zone}
          </p>
        </div>
        <CameraHealthBadge health={camera.health} />
      </header>
      <section className="camera-identity">
        <div>
          <span>Camera reference</span>
          <strong>{camera.id}</strong>
        </div>
        <div>
          <span>Department</span>
          <strong>{camera.departmentRef}</strong>
        </div>
        <div>
          <span>Configuration</span>
          <strong>{camera.configured ? "Configured" : "Unavailable"}</strong>
        </div>
        <div>
          <span>Source state</span>
          <strong>{camera.state}</strong>
        </div>
      </section>
      <div className="detail-columns">
        <CapabilitySummary stream={stream} />
        <DiagnosticsTimeline stream={stream} />
      </div>
      <section className="detail-panel">
        <header>
          <div>
            <span className="eyebrow">CONNECTED WORKSPACE</span>
            <h2>Primary generated stream</h2>
          </div>
          <RadioTower size={18} />
        </header>
        <div className="stream-row">
          <div>
            <strong>{stream.label}</strong>
            <small>{stream.id}</small>
          </div>
          <span>{stream.state}</span>
          <span>{stream.preferredTransport.toUpperCase()}</span>
          <Link className="primary-link" to={`/operations/diagnostics/${stream.id}`}>
            Open diagnostics
          </Link>
        </div>
      </section>
    </>
  );
}
