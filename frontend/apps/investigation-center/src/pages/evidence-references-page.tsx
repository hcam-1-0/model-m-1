import { FileLock2 } from "lucide-react";
import { AuthorityLimit } from "../components/authority-limit";
import { EvidenceHandoff } from "../components/evidence-handoff";
import { evidenceReferences } from "../data/investigation-projections";
export function EvidenceReferencesPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INVESTIGATION / EVIDENCE REFERENCES</p>
          <h1>Evidence reference handoff</h1>
          <p>
            Opaque references only. Evidence Desk independently checks department, purpose, role,
            capability, and object scope.
          </p>
        </div>
        <span className="page-icon">
          <FileLock2 size={19} /> unresolved
        </span>
      </header>
      <AuthorityLimit compact />
      <section className="evidence-list" aria-label="Generated evidence references">
        {evidenceReferences.map((reference) => (
          <EvidenceHandoff key={reference.ref} reference={reference} />
        ))}
      </section>
    </>
  );
}
