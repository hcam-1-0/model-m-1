import { EyeOff, KeyRound } from "lucide-react";
export function SecretReferencePanel() {
  return (
    <section className="panel">
      <header>
        <div>
          <span className="eyebrow">OPAQUE REFERENCE</span>
          <h2>Credential governance</h2>
        </div>
        <KeyRound size={20} />
      </header>
      <dl className="detail-grid">
        <div>
          <dt>Reference</dt>
          <dd>SYN-SECRET-REF-PROVIDER-01</dd>
        </div>
        <div>
          <dt>Provider binding</dt>
          <dd>Declared</dd>
        </div>
        <div>
          <dt>Last rotation evidence</dt>
          <dd>Unavailable</dd>
        </div>
        <div>
          <dt>Secret value</dt>
          <dd>
            <EyeOff size={14} /> Never available
          </dd>
        </div>
      </dl>
      <button type="button" disabled>
        Reveal secret
      </button>
    </section>
  );
}
