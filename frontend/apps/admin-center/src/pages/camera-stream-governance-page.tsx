import { Camera, RadioTower } from "lucide-react";
import { AdminPageFrame } from "../components/admin-state-boundary";
import { NonEffectiveControl } from "../components/non-effective-control";
export function CameraStreamGovernancePage() {
  return (
    <AdminPageFrame
      eyebrow="ADMIN / CAMERA GOVERNANCE"
      title="Camera and stream governance"
      description="Governance projections remain separate from the preserved P5.3 camera catalogue, diagnostics, and view-only live workspaces."
    >
      <section className="summary-band">
        <article>
          <Camera size={18} />
          <span>Camera policies</span>
          <strong>12</strong>
          <small>Generated references</small>
        </article>
        <article>
          <RadioTower size={18} />
          <span>Stream policies</span>
          <strong>18</strong>
          <small>No media access</small>
        </article>
      </section>
      <section className="panel control-list">
        <header>
          <div>
            <span className="eyebrow">NON-EFFECTIVE CONTROLS</span>
            <h2>Governance proposals</h2>
          </div>
        </header>
        <NonEffectiveControl
          label="Camera admission policy"
          detail="Proposal only; no camera connection"
        />
        <NonEffectiveControl
          label="Capability refresh schedule"
          detail="Proposal only; no ONVIF request"
        />
        <NonEffectiveControl
          label="Stream quality ceiling"
          detail="Presentation only; no media mutation"
        />
        <NonEffectiveControl label="Camera retirement" detail="Unavailable; no deletion path" />
      </section>
    </AdminPageFrame>
  );
}
