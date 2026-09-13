import { GisMapShell } from "../components/gis-map-shell";
export function DataRendererHealthPage() {
  return (
    <GisMapShell
      title="Data and renderer health"
      description="Source freshness, renderer admission, degradation, fallback, and recovery visibility."
      compact
    />
  );
}
