import { Database, Radio, ShieldCheck, TriangleAlert } from "lucide-react";
export function SourceStatusStrip() {
  return (
    <section className="source-strip" aria-label="Source status">
      <span>
        <ShieldCheck size={15} /> Contract revision <strong>SYN-REV-P5-2-001</strong>
      </span>
      <span>
        <Database size={15} /> Completeness <strong>Partial</strong>
      </span>
      <span>
        <Radio size={15} /> Live producers <strong>Unavailable</strong>
      </span>
      <span>
        <TriangleAlert size={15} /> Blocked producer gaps <strong>14</strong>
      </span>
    </section>
  );
}
