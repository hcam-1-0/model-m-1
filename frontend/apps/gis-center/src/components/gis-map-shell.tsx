import { useEffect, useMemo, useRef, useState } from "react";
import type { ResourceProfile } from "@hcam/capabilities";
import type { ResourceId } from "@hcam/contracts";
import type { GisFeatureSummary, GisLayerDefinition, GisRendererMode } from "@hcam/gis-contracts";
import { admitRenderer } from "@hcam/gis-domain";
import { createDeckOverlay, mountMapLibre, type MapLibreController } from "@hcam/gis-renderers";
import { generatedGisFeatures, generatedLayers } from "@hcam/test-fixtures";
import { AccessibleFeatureTable } from "./accessible-feature-table";
import { FeatureInspector } from "./feature-inspector";
import { LayerExplorer } from "./layer-explorer";
import { RendererHealth } from "./renderer-health";
import { SourceStatus } from "./source-status";
import { SpatialFilterBar } from "./spatial-filter-bar";
import { TemporalControls } from "./temporal-controls";
import { WorkspaceStrip } from "./workspace-strip";
export function GisMapShell({
  title,
  description,
  compact = false,
}: {
  readonly title: string;
  readonly description: string;
  readonly compact?: boolean;
}) {
  const [profile, setProfile] = useState<ResourceProfile>("enhanced");
  const [requested, setRequested] = useState<GisRendererMode>("deck_overlaid");
  const [query, setQuery] = useState("");
  const [sourceState, setSourceState] = useState<"all" | "available" | "unavailable" | "unknown">(
    "all",
  );
  const [selected, setSelected] = useState<ResourceId | null>(null);
  const [visible, setVisible] = useState<ReadonlySet<string>>(
    () => new Set(generatedLayers.filter((item) => item.defaultVisible).map((item) => item.id)),
  );
  const container = useRef<HTMLDivElement>(null);
  const controller = useRef<MapLibreController | null>(null);
  const features = useMemo(
    () => generatedGisFeatures(compact ? 10 : 50) as readonly GisFeatureSummary[],
    [compact],
  );
  const layers = generatedLayers as readonly GisLayerDefinition[];
  const filtered = useMemo(
    () =>
      features.filter(
        (feature) =>
          feature.label.toLowerCase().includes(query.toLowerCase()) &&
          (sourceState === "all" || feature.status === sourceState),
      ),
    [features, query, sourceState],
  );
  const supportsWebGl = typeof WebGLRenderingContext !== "undefined";
  const supportsWebGl2 = typeof WebGL2RenderingContext !== "undefined";
  const admission = admitRenderer({
    requested,
    profile,
    webgl: supportsWebGl,
    webgl2: supportsWebGl2,
    policyAllowed: true,
    healthy: true,
  });
  useEffect(() => {
    if (!container.current || admission.mode === "list_only") return;
    const mounted = mountMapLibre(container.current, filtered, setSelected);
    controller.current = mounted;
    if (admission.mode === "deck_overlaid" || admission.mode === "deck_interleaved")
      void createDeckOverlay(filtered, admission.mode)
        .then((overlay) => {
          if (controller.current === mounted)
            mounted.map.addControl(overlay as Parameters<typeof mounted.map.addControl>[0]);
        })
        .catch(() => undefined);
    return () => {
      mounted.dispose();
      if (controller.current === mounted) controller.current = null;
    };
  }, [admission.mode, filtered]);
  const choose = (id: ResourceId) => {
    setSelected(id);
    controller.current?.focus(id);
  };
  const selectedFeature = features.find((feature) => feature.id === selected) ?? null;
  return (
    <>
      <div className="gis-page-heading">
        <div>
          <small>CONNECTED GIS CENTER</small>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <div className="renderer-selects">
          <label>
            Profile
            <select
              value={profile}
              onChange={(event) => setProfile(event.currentTarget.value as ResourceProfile)}
            >
              <option value="low_resource">Low resource</option>
              <option value="enhanced">Enhanced</option>
              <option value="control_room">Control room</option>
              <option value="future_server">Future server</option>
            </select>
          </label>
          <label>
            Renderer
            <select
              value={requested}
              onChange={(event) => setRequested(event.currentTarget.value as GisRendererMode)}
            >
              <option value="maplibre">MapLibre 2D</option>
              <option value="deck_overlaid">deck.gl overlay</option>
              <option value="deck_interleaved">deck.gl interleaved</option>
              <option value="list_only">List only</option>
            </select>
          </label>
        </div>
      </div>
      <SourceStatus />
      <WorkspaceStrip />
      <SpatialFilterBar
        query={query}
        onQuery={setQuery}
        sourceState={sourceState}
        onSourceState={setSourceState}
        onFit={() => controller.current?.fit()}
      />
      <div className="gis-workbench">
        <aside aria-label="GIS layers and renderer controls" className="layer-rail">
          <LayerExplorer
            layers={layers}
            visible={visible}
            onToggle={(id) =>
              setVisible((current) => {
                const next = new Set(current);
                if (next.has(id)) next.delete(id);
                else next.add(id);
                return next;
              })
            }
          />
          <RendererHealth admission={admission} />
        </aside>
        <section className="map-stage" aria-label="Generated GIS canvas">
          {admission.mode === "list_only" ? (
            <div className="map-unavailable">
              <MapFallback />
              <strong>Map renderer unavailable by selected policy or capability.</strong>
              <span>The authoritative table remains complete.</span>
            </div>
          ) : (
            <div className="map-canvas" ref={container} data-testid="gis-map" />
          )}
          <div className="map-legend">
            <span>
              <i className="green" />
              Information
            </span>
            <span>
              <i className="amber" />
              Attention
            </span>
            <span>
              <i className="red" />
              Critical
            </span>
            <strong>Generated only</strong>
          </div>
        </section>
        <FeatureInspector feature={selectedFeature} onClose={() => setSelected(null)} />
      </div>
      <TemporalControls />
      <AccessibleFeatureTable features={filtered} selected={selected} onSelect={choose} />
    </>
  );
}
function MapFallback() {
  return (
    <svg width="54" height="54" viewBox="0 0 54 54" aria-hidden="true">
      <path
        d="M5 13l14-7 16 7 14-7v35l-14 7-16-7-14 7z"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      />
      <path d="M19 6v35M35 13v35" fill="none" stroke="currentColor" />
    </svg>
  );
}
