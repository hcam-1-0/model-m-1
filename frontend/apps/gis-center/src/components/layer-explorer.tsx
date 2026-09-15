import { Eye, EyeOff, Layers3 } from "lucide-react";
import type { GisLayerDefinition } from "@hcam/gis-contracts";
export function LayerExplorer({
  layers,
  visible,
  onToggle,
}: {
  readonly layers: readonly GisLayerDefinition[];
  readonly visible: ReadonlySet<string>;
  readonly onToggle: (id: string) => void;
}) {
  return (
    <section className="tool-section">
      <h2>
        <Layers3 size={16} />
        Layers
      </h2>
      <ul className="layer-list">
        {layers.map((layer) => (
          <li key={layer.id}>
            <button
              type="button"
              aria-pressed={visible.has(layer.id)}
              onClick={() => onToggle(layer.id)}
            >
              {visible.has(layer.id) ? <Eye size={15} /> : <EyeOff size={15} />}
              <span>
                <strong>{layer.label}</strong>
                <small>{layer.kinds.join(", ")}</small>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
