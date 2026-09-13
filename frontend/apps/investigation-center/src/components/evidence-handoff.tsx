import { ArrowUpRight, FileLock2, ShieldCheck } from "lucide-react";
import type { EvidenceReference } from "../../../../packages/investigation-contracts/src";
export function EvidenceHandoff({ reference }: { readonly reference: EvidenceReference }) {
  return (
    <article className="evidence-handoff">
      <div className="evidence-icon">
        <FileLock2 size={19} />
      </div>
      <div>
        <strong>{reference.label}</strong>
        <code>{reference.ref}</code>
        <span>
          {reference.category.replaceAll("_", " ")} / {reference.availability}
        </span>
      </div>
      <div className="evidence-boundary">
        <ShieldCheck size={14} /> Source unresolved
      </div>
      <a
        href={`http://127.0.0.1:4177/evidence/${reference.ref}`}
        aria-label={`Open ${reference.label} in independently authorized Evidence Desk`}
      >
        <ArrowUpRight size={17} />
      </a>
    </article>
  );
}
