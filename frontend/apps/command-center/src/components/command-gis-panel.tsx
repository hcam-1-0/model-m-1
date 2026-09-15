import { useEffect, useRef, useState } from "react";
import { List, Map as MapIcon } from "lucide-react";
import type { ResourceId } from "@hcam/contracts";
import type { GisFeatureSummary } from "@hcam/gis-contracts";
import { mountMapLibre, type MapLibreController } from "@hcam/gis-renderers";
export function CommandGisPanel({ features }: { readonly features: readonly GisFeatureSummary[] }) {
  const container = useRef<HTMLDivElement>(null);
  const controller = useRef<MapLibreController | null>(null);
  const [selected, setSelected] = useState<ResourceId | null>(null);
  useEffect(() => {
    if (!container.current) return;
    controller.current = mountMapLibre(container.current, features, setSelected);
    return () => {
      controller.current?.dispose();
      controller.current = null;
    };
  }, [features]);
  return (
    <section className="panel map-panel">
      <header>
        <div>
          <p className="eyebrow">CONNECTED GIS</p>
          <h2>Situation geography</h2>
        </div>
        <a href="http://127.0.0.1:4174/gis">
          <MapIcon size={15} /> Open GIS Center
        </a>
      </header>
      <div
        className="embedded-map"
        ref={container}
        role="region"
        aria-label="Generated situation map"
      />
      <div className="map-list">
        <h3>
          <List size={15} /> Authoritative map alternative
        </h3>
        <ul>
          {features.slice(0, 5).map((feature) => (
            <li key={feature.id}>
              <button
                type="button"
                aria-pressed={selected === feature.id}
                onClick={() => {
                  setSelected(feature.id);
                  controller.current?.focus(feature.id);
                }}
              >
                <span>{feature.label}</span>
                <small>
                  {feature.kind} · {feature.status}
                </small>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
