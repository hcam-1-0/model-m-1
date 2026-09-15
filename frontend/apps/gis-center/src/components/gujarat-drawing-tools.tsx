import {
  Check,
  Circle,
  Download,
  MousePointer2,
  Pentagon,
  Pencil,
  RotateCcw,
  Spline,
  Square,
  Trash2,
  Undo2,
  X,
} from "lucide-react";
import type { DrawMode, DrawProgress, DrawnShape } from "@hcam/gis-domain";
import { formatArea, formatDistance } from "@hcam/gis-domain";

interface HcamDrawingToolsProps {
  mode: DrawMode | null;
  progress: DrawProgress | null;
  shapes: DrawnShape[];
  cameraCountInAreas: Record<string, number>;
  onSetMode: (mode: DrawMode | null) => void;
  onCommand: (action: "undo" | "finish" | "cancel") => void;
  onRename: (id: string, name: string) => void;
  onDelete: (id: string) => void;
  onClear: () => void;
  onExport: () => void;
  onClose: () => void;
}

const MODES: { id: DrawMode; label: string; hint: string; Icon: typeof Pentagon }[] = [
  { id: "polygon", label: "Area", hint: "Any shape, corner by corner", Icon: Pentagon },
  { id: "rectangle", label: "Box", hint: "Two clicks, opposite corners", Icon: Square },
  { id: "circle", label: "Radius", hint: "Centre, then distance out", Icon: Circle },
  { id: "line", label: "Path", hint: "Measure a route", Icon: Spline },
];

const MODE_INSTRUCTION: Record<DrawMode, string> = {
  polygon: "Click corners. Double-click or Finish to close the area.",
  rectangle: "Click one corner, then the opposite corner.",
  circle: "Click a centre point, then click the radius edge.",
  line: "Click waypoints. Double-click or Finish to end the path.",
};

export function GujaratDrawingTools({
  mode,
  progress,
  shapes,
  cameraCountInAreas,
  onSetMode,
  onCommand,
  onRename,
  onDelete,
  onClear,
  onExport,
  onClose,
}: HcamDrawingToolsProps) {
  const totalArea = shapes.reduce((sum, shape) => sum + shape.areaKm2, 0);
  const totalPerimeter = shapes.reduce((sum, shape) => sum + shape.perimeterKm, 0);
  const canFinish = progress?.closable ?? false;
  const canUndo = (progress?.vertices ?? 0) > 0;

  return (
    <section className="hcam-drawing-panel" aria-label="Drawing tools">
      <header className="hcam-drawing-header">
        <span>
          <Pentagon size={15} /> Drawing tools
        </span>
        <button type="button" onClick={onClose} aria-label="Close drawing tools">
          <X size={15} />
        </button>
      </header>
      <div className="hcam-drawing-metrics">
        <div>
          <span>Tracked area</span>
          <strong>{formatArea(totalArea)}</strong>
        </div>
        <div>
          <span>AOIs / perim</span>
          <strong>
            {shapes.length} / {formatDistance(totalPerimeter)}
          </strong>
        </div>
      </div>
      <div className="hcam-drawing-step">
        <span>{mode ? "Step 2 — click the map" : "Step 1 — choose a shape"}</span>
        <div className="hcam-drawing-modes">
          {MODES.map(({ id, label, hint, Icon }) => (
            <button
              type="button"
              key={id}
              className={mode === id ? "is-active" : ""}
              onClick={() => onSetMode(mode === id ? null : id)}
            >
              <Icon size={16} />
              <strong>{label}</strong>
              <small>{hint}</small>
            </button>
          ))}
        </div>
      </div>
      {mode ? (
        <div className="hcam-drawing-active">
          <div>
            <MousePointer2 size={15} />
            <span>{MODE_INSTRUCTION[mode]}</span>
          </div>
          {progress ? (
            <p>
              {progress.radiusKm ? `r ${formatDistance(progress.radiusKm)} · ` : ""}
              {progress.areaKm2 ? `${formatArea(progress.areaKm2)} · ` : ""}
              {progress.lengthKm ? formatDistance(progress.lengthKm) : ""}
              {progress.vertices ? ` · ${progress.vertices} points` : ""}
            </p>
          ) : null}
          <div className="hcam-drawing-actions">
            <button type="button" onClick={() => onCommand("undo")} disabled={!canUndo}>
              <Undo2 size={13} /> Undo
            </button>
            {mode !== "rectangle" && mode !== "circle" ? (
              <button
                type="button"
                onClick={() => onCommand("finish")}
                disabled={!canFinish}
                className="is-primary"
              >
                <Check size={13} /> Finish
              </button>
            ) : null}
            <button type="button" onClick={() => onCommand("cancel")}>
              <X size={13} /> Cancel
            </button>
          </div>
          <small>Enter finishes · Backspace undoes · Esc cancels</small>
        </div>
      ) : null}
      <div className="hcam-drawing-saved">
        <div className="hcam-drawing-saved-heading">
          <span>Saved drawings</span>
          {shapes.length ? (
            <div>
              <button
                type="button"
                onClick={onExport}
                title="Export all generated drawings as GeoJSON"
              >
                <Download size={13} /> Export
              </button>
              <button type="button" onClick={onClear} title="Clear all drawings">
                <Trash2 size={13} /> Clear
              </button>
            </div>
          ) : null}
        </div>
        {shapes.length ? (
          <ul>
            {shapes.map((shape) => {
              const cameras = cameraCountInAreas[shape.id];
              return (
                <ShapeRow
                  key={shape.id}
                  shape={shape}
                  {...(cameras === undefined ? {} : { cameras })}
                  onRename={onRename}
                  onDelete={onDelete}
                />
              );
            })}
          </ul>
        ) : (
          <p className="hcam-drawing-empty">
            <RotateCcw size={19} />
            Choose a shape above, then click the map to measure an area or route.
          </p>
        )}
      </div>
    </section>
  );
}

function ShapeRow({
  shape,
  cameras,
  onRename,
  onDelete,
}: {
  shape: DrawnShape;
  cameras?: number;
  onRename: (id: string, name: string) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <li>
      <span className="hcam-drawing-colour" style={{ background: shape.color }} />
      <div>
        <strong>{shape.name}</strong>
        <small>
          {shape.kind === "line"
            ? formatDistance(shape.perimeterKm)
            : `${formatArea(shape.areaKm2)} · ${formatDistance(shape.perimeterKm)}`}
          {cameras !== undefined ? ` · ${cameras} visible cameras` : ""}
        </small>
      </div>
      <button
        type="button"
        title="Rename drawing"
        onClick={() => {
          const name = window.prompt("Drawing name", shape.name);
          if (name?.trim()) onRename(shape.id, name.trim());
        }}
      >
        <Pencil size={12} />
      </button>
      <button type="button" title="Delete drawing" onClick={() => onDelete(shape.id)}>
        <Trash2 size={12} />
      </button>
    </li>
  );
}
