import { History } from "lucide-react";
import { AuthorityLimit } from "../components/authority-limit";
import { ReconstructionPanel } from "../components/reconstruction-panel";
import { TimelineTable } from "../components/timeline-table";
import { reconstructionBefore } from "../data/investigation-projections";
export function ReconstructionPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INVESTIGATION / RECONSTRUCTION</p>
          <h1>Exact revision reconstruction</h1>
          <p>
            Server-projected generated state at one revision, with digest, completeness, omissions,
            limitations, and later-change warning.
          </p>
        </div>
        <span className="page-icon">
          <History size={19} /> exact revision
        </span>
      </header>
      <AuthorityLimit compact />
      <ReconstructionPanel value={reconstructionBefore} />
      <section className="panel table-panel">
        <header>
          <div>
            <span className="eyebrow">INCLUDED CHRONOLOGY</span>
            <h2>Revision-bound records</h2>
          </div>
          <code>{reconstructionBefore.resolvedRevision}</code>
        </header>
        <TimelineTable entries={reconstructionBefore.timeline.slice(0, 10)} />
      </section>
    </>
  );
}
