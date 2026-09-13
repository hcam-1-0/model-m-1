import { FileLock2 } from "lucide-react";
export function PolicyPreviewPanel({ policy = "SYN-POLICY-R7" }: { readonly policy?: string }) {
  return (
    <section className="panel">
      <header>
        <div>
          <span className="eyebrow">POLICY PROJECTION</span>
          <h2>{policy}</h2>
        </div>
        <FileLock2 size={20} />
      </header>
      <dl className="detail-grid">
        <div>
          <dt>Evaluation</dt>
          <dd>Default deny</dd>
        </div>
        <div>
          <dt>ABAC</dt>
          <dd>Department + purpose constrained</dd>
        </div>
        <div>
          <dt>Database boundary</dt>
          <dd>RLS equivalence required</dd>
        </div>
        <div>
          <dt>Activation</dt>
          <dd>Unavailable</dd>
        </div>
      </dl>
    </section>
  );
}
