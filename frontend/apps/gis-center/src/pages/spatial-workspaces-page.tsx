import { GisMapShell } from "../components/gis-map-shell";
export function SpatialWorkspacesPage() {
  return (
    <GisMapShell
      title="Spatial workspaces"
      description="Display-only generated workspace state; save and share mutations remain disabled."
      compact
    />
  );
}
