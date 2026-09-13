import { Fingerprint } from "lucide-react";
import {
  integrityPresentation,
  orderVerificationHistory,
} from "../../../../packages/evidence-domain/src";
import type {
  EvidenceReference,
  EvidenceVerificationEvent,
} from "../../../../packages/investigation-contracts/src";

export function IntegrityHistory({
  reference,
  events,
}: {
  readonly reference: EvidenceReference;
  readonly events: readonly EvidenceVerificationEvent[];
}) {
  const presentation = integrityPresentation(reference);
  return (
    <section className="panel table-panel">
      <header>
        <div>
          <span className="eyebrow">OBSERVATION HISTORY</span>
          <h2>Integrity checks</h2>
        </div>
        <Fingerprint size={19} />
      </header>
      <div className="integrity-caution">
        <strong>{presentation.label}</strong>
        <span>
          {presentation.caution} It does not establish truth, authenticity, or admissibility.
        </span>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Sequence</th>
              <th>Observed at</th>
              <th>Outcome</th>
              <th>Digest observation</th>
              <th>Truth</th>
            </tr>
          </thead>
          <tbody>
            {orderVerificationHistory(events).map((event) => (
              <tr key={event.ref}>
                <td>{event.sequence}</td>
                <td>
                  <time>{event.observedAt}</time>
                </td>
                <td>
                  <span className={`status-chip status-${event.outcome}`}>
                    {event.outcome.replaceAll("_", " ")}
                  </span>
                </td>
                <td>
                  <code>{event.digestObservation ?? "not observed"}</code>
                </td>
                <td>Not established</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
