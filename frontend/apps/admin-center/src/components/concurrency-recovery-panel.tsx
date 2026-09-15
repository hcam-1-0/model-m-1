import { RefreshCw } from "lucide-react";
export function ConcurrencyRecoveryPanel() {
  return (
    <section className="panel">
      <header>
        <div>
          <span className="eyebrow">CONFLICT RECOVERY</span>
          <h2>Revision changed</h2>
        </div>
        <RefreshCw size={20} />
      </header>
      <p>The authoritative revision changed after this generated draft was opened.</p>
      <dl className="detail-grid">
        <div>
          <dt>Expected ETag</dt>
          <dd>&quot;SYN-P56-CHANGE-4&quot;</dd>
        </div>
        <div>
          <dt>Current ETag</dt>
          <dd>&quot;SYN-P56-CHANGE-5&quot;</dd>
        </div>
        <div>
          <dt>Automatic retry</dt>
          <dd>Disabled</dd>
        </div>
        <div>
          <dt>Required action</dt>
          <dd>Refetch, compare, reconsider</dd>
        </div>
      </dl>
      <button type="button">Review generated comparison</button>
    </section>
  );
}
