import { useState } from "react";
import { SpatialIntelligencePanel } from "../components/spatial-intelligence-panel";
import { spatial } from "../data/intelligence-projections";
export function SpatialIntelligencePage() {
  const [selected, setSelected] = useState<string | null>(spatial.records[0]?.ref ?? null);
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">ANALYSIS / SPATIAL</p>
          <h1>Spatial intelligence</h1>
          <p>
            Connected to the shared GIS meaning model while keeping the Intelligence Center
            subordinate to Command.
          </p>
        </div>
        <a className="primary-link" href="http://127.0.0.1:4174/gis">
          Open specialist GIS Center
        </a>
      </header>
      <SpatialIntelligencePanel projection={spatial} selected={selected} onSelect={setSelected} />
    </>
  );
}
