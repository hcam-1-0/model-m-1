import type { AdmissionDecision, ResourceProfile } from "@hcam/camera-live-domain";
import { Gauge, MonitorPlay, ShieldCheck, Video } from "lucide-react";

export function AdmissionBudgetStrip({
  profile,
  decisions,
}: {
  readonly profile: ResourceProfile;
  readonly decisions: readonly AdmissionDecision[];
}) {
  const admitted = decisions.filter((decision) => decision.admitted).length;
  return (
    <div className="admission-strip" aria-label="Media admission summary">
      <span>
        <Gauge size={16} />
        <small>Profile</small>
        <strong>{profile.id.replaceAll("_", " ")}</strong>
      </span>
      <span>
        <MonitorPlay size={16} />
        <small>Admitted</small>
        <strong>
          {admitted} / {profile.maxStreams}
        </strong>
      </span>
      <span>
        <ShieldCheck size={16} />
        <small>Policy</small>
        <strong>View only</strong>
      </span>
      <span>
        <Video size={16} />
        <small>Rendition ceiling</small>
        <strong>{profile.preferredRendition}</strong>
      </span>
    </div>
  );
}
