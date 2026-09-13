import { Ban, EyeOff, FileLock2 } from "lucide-react";
import type { EvidenceReference } from "../../../../packages/investigation-contracts/src";

export function SourceBoundaryPanel({ reference }: { readonly reference: EvidenceReference }) {
  return (
    <section className="panel source-boundary">
      <header>
        <div>
          <span className="eyebrow">OPAQUE SOURCE BOUNDARY</span>
          <h2>Source reference</h2>
        </div>
        <FileLock2 size={19} />
      </header>
      <p>Source operations unavailable. No source bytes are retained in this workspace.</p>
      <dl>
        <div>
          <dt>Reference</dt>
          <dd>
            <code>{reference.source.referenceId}</code>
          </dd>
        </div>
        <div>
          <dt>Resolution</dt>
          <dd>
            <Ban size={14} /> unavailable
          </dd>
        </div>
        <div>
          <dt>Rendering</dt>
          <dd>
            <EyeOff size={14} /> unavailable
          </dd>
        </div>
        <div>
          <dt>Download</dt>
          <dd>
            <Ban size={14} /> unavailable
          </dd>
        </div>
        <div>
          <dt>Locator</dt>
          <dd>not exposed</dd>
        </div>
      </dl>
    </section>
  );
}
