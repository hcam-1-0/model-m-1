import { EvidenceLimitations } from "../components/evidence-limitations";
import { IntegrityHistory } from "../components/integrity-history";
import { selectedEvidence, verificationHistory } from "../data/evidence-projections";

export function IntegrityHistoryPage() {
  if (!selectedEvidence) return null;
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">APPEND-ONLY OBSERVATIONS</p>
          <h1>Integrity history</h1>
          <p>
            Each generated digest observation remains separately recorded. Later observations do not
            erase earlier outcomes.
          </p>
        </div>
      </header>
      <IntegrityHistory reference={selectedEvidence} events={verificationHistory} />
      <EvidenceLimitations
        limitations={[
          "A matching digest does not establish authenticity, event truth, identity, guilt, or legal admissibility.",
        ]}
      />
    </>
  );
}
