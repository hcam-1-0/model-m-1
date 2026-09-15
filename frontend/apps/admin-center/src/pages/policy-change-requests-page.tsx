import { useState } from "react";
import { ApprovalTimeline } from "../components/approval-timeline";
import { AdminPageFrame } from "../components/admin-state-boundary";
import { ChangeImpactPanel } from "../components/change-impact-panel";
import { ConcurrencyRecoveryPanel } from "../components/concurrency-recovery-panel";
import { changeRequests } from "../data/admin-projections";
export function PolicyChangeRequestsPage() {
  const [selected, setSelected] = useState(() => changeRequests.at(0));
  if (!selected) return null;
  return (
    <AdminPageFrame
      eyebrow="ADMIN / CHANGE CONTROL"
      title="Policy and change requests"
      description="Typed, revisioned, generated-only requests with independent review, strong concurrency, and no automatic activation."
    >
      <div className="master-detail">
        <section className="panel list-panel">
          <header>
            <div>
              <span className="eyebrow">CHANGE QUEUE</span>
              <h2>{changeRequests.length} requests</h2>
            </div>
          </header>
          <ul className="record-list">
            {changeRequests.map((item) => (
              <li key={item.ref}>
                <button
                  type="button"
                  className={item.ref === selected.ref ? "selected" : ""}
                  onClick={() => setSelected(item)}
                >
                  <strong>{item.kind.replaceAll("_", " ")}</strong>
                  <span>{item.ref}</span>
                  <small>{item.status.replaceAll("_", " ")}</small>
                </button>
              </li>
            ))}
          </ul>
        </section>
        <div className="detail-stack">
          <section className="panel">
            <header>
              <div>
                <span className="eyebrow">SELECTED REQUEST</span>
                <h2>{selected.ref}</h2>
              </div>
              <span className="status partial">{selected.status.replaceAll("_", " ")}</span>
            </header>
            <ApprovalTimeline request={selected} />
            <dl className="detail-grid">
              <div>
                <dt>Requester</dt>
                <dd>{selected.requesterRef}</dd>
              </div>
              <div>
                <dt>Policy</dt>
                <dd>{selected.policyRevision}</dd>
              </div>
              <div>
                <dt>Revision</dt>
                <dd>{selected.resourceRevision}</dd>
              </div>
              <div>
                <dt>Effect applied</dt>
                <dd>No</dd>
              </div>
            </dl>
            <button type="button">Open generated review</button>
          </section>
          <ChangeImpactPanel impacts={selected.impactSummary} />
          <ConcurrencyRecoveryPanel />
        </div>
      </div>
    </AdminPageFrame>
  );
}
