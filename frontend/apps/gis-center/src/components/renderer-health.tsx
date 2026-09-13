import type { GisAdmission } from "@hcam/gis-contracts";
export function RendererHealth({ admission }: { readonly admission: GisAdmission }) {
  return (
    <div className="renderer-health" role="status">
      <span className={admission.mode === "list_only" ? "health-dot warning" : "health-dot"} />
      <div>
        <small>Renderer mode</small>
        <strong>{admission.mode.replaceAll("_", " ")}</strong>
      </div>
      <div>
        <small>Admission</small>
        <strong>{admission.reason.replaceAll("_", " ")}</strong>
      </div>
      <div>
        <small>Fallback</small>
        <strong>Always available</strong>
      </div>
    </div>
  );
}
