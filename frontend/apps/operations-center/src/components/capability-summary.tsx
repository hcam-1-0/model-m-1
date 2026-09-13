import { Boxes, Clock3, RadioTower, Video } from "lucide-react";
import type { StreamProjection } from "@hcam/camera-live-domain";

export function CapabilitySummary({ stream }: { readonly stream: StreamProjection }) {
  const capability = stream.capabilities;
  return (
    <section className="detail-panel" aria-labelledby="capability-title">
      <header>
        <div>
          <span className="eyebrow">READ-ONLY INVENTORY</span>
          <h2 id="capability-title">Stream capability</h2>
        </div>
        <span className={`truth ${capability.status}`}>{capability.status}</span>
      </header>
      <dl className="definition-grid">
        <div>
          <dt>
            <RadioTower size={15} /> Transports
          </dt>
          <dd>{capability.transports.join(", ").toUpperCase() || "Unknown"}</dd>
        </div>
        <div>
          <dt>
            <Video size={15} /> Codecs
          </dt>
          <dd>{capability.codecs.join(", ") || "Unknown"}</dd>
        </div>
        <div>
          <dt>
            <Boxes size={15} /> Profiles
          </dt>
          <dd>{capability.profileCount ?? "Unknown"}</dd>
        </div>
        <div>
          <dt>
            <Clock3 size={15} /> Observed
          </dt>
          <dd>{capability.observedAt?.replace("T", " ").slice(0, 16) ?? "Unavailable"}</dd>
        </div>
      </dl>
      {capability.mediaOnly ? (
        <p className="inline-notice">
          Media-only capability snapshot. Device-management information is unavailable.
        </p>
      ) : null}
    </section>
  );
}
