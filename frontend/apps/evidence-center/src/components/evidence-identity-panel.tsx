import { FileLock2 } from "lucide-react";
import type { EvidenceReference } from "../../../../packages/investigation-contracts/src";

export function EvidenceIdentityPanel({ reference }: { readonly reference: EvidenceReference }) {
  return (
    <header className="identity-band">
      <div className="identity-icon">
        <FileLock2 size={22} />
      </div>
      <div>
        <p className="eyebrow">GENERATED EVIDENCE REFERENCE</p>
        <h1>{reference.label}</h1>
        <code>{reference.ref}</code>
      </div>
      <div>
        <span className={`status-chip status-${reference.availability}`}>
          {reference.availability}
        </span>
        <small>revision {reference.revision}</small>
      </div>
    </header>
  );
}
