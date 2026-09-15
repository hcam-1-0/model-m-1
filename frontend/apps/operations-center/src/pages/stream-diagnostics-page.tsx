import { ArrowLeft, FileSearch, ShieldCheck } from "lucide-react";
import { Link, useParams } from "react-router";
import { CapabilitySummary } from "../components/capability-summary";
import { DiagnosticsTimeline } from "../components/diagnostics-timeline";
import { StateBoundary } from "../components/state-boundary";
import { cameraByStream } from "../data/camera-live-projections";

export function StreamDiagnosticsPage() {
  const { streamId } = useParams();
  const camera = cameraByStream(streamId);
  if (!camera)
    return (
      <StateBoundary state="empty">
        <span />
      </StateBoundary>
    );
  const stream = camera.streams.find((item) => item.id === streamId);
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
          <Link className="back-link" to={`/operations/cameras/${camera.id}`}>
            <ArrowLeft size={15} /> {camera.label}
          </Link>
          <p className="eyebrow">STREAM DIAGNOSTICS / GENERATED</p>
          <h1>{stream.label}</h1>
          <p>Read-only capability, probe, freshness, and recovery projection.</p>
        </div>
        <span className="safe-mode">
          <ShieldCheck size={16} /> Metadata only
        </span>
      </header>
      <div className="detail-columns">
        <CapabilitySummary stream={stream} />
        <DiagnosticsTimeline stream={stream} />
      </div>
      <section className="detail-panel">
        <header>
          <div>
            <span className="eyebrow">CONNECTION POLICY</span>
            <h2>Effective diagnostic boundary</h2>
          </div>
          <FileSearch size={18} />
        </header>
        <dl className="policy-list">
          <div>
            <dt>Endpoint exposure</dt>
            <dd>Opaque grant only</dd>
          </div>
          <div>
            <dt>Recording</dt>
            <dd>Disabled</dd>
          </div>
          <div>
            <dt>Snapshots</dt>
            <dd>Disabled</dd>
          </div>
          <div>
            <dt>PTZ and control</dt>
            <dd>Disabled</dd>
          </div>
          <div>
            <dt>Retention</dt>
            <dd>Zero media retention</dd>
          </div>
        </dl>
      </section>
    </>
  );
}
