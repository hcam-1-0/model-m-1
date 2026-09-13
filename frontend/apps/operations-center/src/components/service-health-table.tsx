import type { ServiceHealth } from "../../../../packages/operations-contracts/src";
export function ServiceHealthTable({ services }: { readonly services: readonly ServiceHealth[] }) {
  return (
    <div className="table-scroll" tabIndex={0}>
      <table className="platform-table">
        <thead>
          <tr>
            <th>Service</th>
            <th>Domain</th>
            <th>State</th>
            <th>Latency</th>
            <th>Saturation</th>
            <th>Freshness</th>
          </tr>
        </thead>
        <tbody>
          {services.map((item) => (
            <tr key={item.ref}>
              <td>
                <strong>{item.label}</strong>
                <small>{item.ref}</small>
              </td>
              <td>{item.domain}</td>
              <td>
                <span className={`truth ${item.state}`}>{item.state}</span>
              </td>
              <td>{item.latencyBucket}</td>
              <td>{item.saturationBand}</td>
              <td>
                {item.truth.completeness}
                <small>generated only</small>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
