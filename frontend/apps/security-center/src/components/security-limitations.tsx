import { ShieldAlert } from "lucide-react";
export function SecurityLimitations() {
  return (
    <aside className="limitations" role="note">
      <ShieldAlert size={20} />
      <div>
        <strong>Assurance boundary</strong>
        <p>
          Generated posture does not establish absence of risk, compliance, compromise, production
          readiness, or operational security status.
        </p>
      </div>
    </aside>
  );
}
