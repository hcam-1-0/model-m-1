import { Network } from "lucide-react";
import { InvestigationRelationshipPanel } from "../components/investigation-relationship-panel";
import { InvestigationRelationshipTable } from "../components/investigation-relationship-table";
import { investigationRelationships } from "../data/investigation-projections";
export function InvestigationRelationshipsPage() {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">INVESTIGATION / RELATIONSHIPS</p>
          <h1>Bounded relationship view</h1>
          <p>
            Generated provenance relationships are a visual aid. Node and edge tables are the
            complete authoritative representation.
          </p>
        </div>
        <span className="page-icon">
          <Network size={19} /> bounded graph
        </span>
      </header>
      <InvestigationRelationshipPanel projection={investigationRelationships} />
      <InvestigationRelationshipTable projection={investigationRelationships} />
    </>
  );
}
