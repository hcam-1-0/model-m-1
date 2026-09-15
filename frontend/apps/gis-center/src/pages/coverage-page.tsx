import { GisMapShell } from "../components/gis-map-shell";
export function CoveragePage() {
  return (
    <GisMapShell
      title="Coverage and blind spots"
      description="Server-authored generated coverage states; the client does not infer coverage or risk."
    />
  );
}
