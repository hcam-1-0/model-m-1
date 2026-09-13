import { queueDisposition } from "../../../../packages/platform-operations-domain/src";
import { platformQueues } from "../data/platform-operations-projections";
export function QueueWorkerTable() {
  return (
    <div className="table-scroll" tabIndex={0}>
      <table className="platform-table">
        <thead>
          <tr>
            <th>Queue</th>
            <th>Depth</th>
            <th>Oldest</th>
            <th>Lease</th>
            <th>Retries</th>
            <th>Disposition</th>
          </tr>
        </thead>
        <tbody>
          {platformQueues.map((item) => (
            <tr key={item.ref}>
              <td>
                <strong>{item.label}</strong>
                <small>{item.ref}</small>
              </td>
              <td>{item.depthBand}</td>
              <td>{item.oldestAgeBand}</td>
              <td>{item.leaseState}</td>
              <td>{item.retryBand}</td>
              <td>
                <span className={`truth ${queueDisposition(item)}`}>
                  {queueDisposition(item).replaceAll("_", " ")}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
