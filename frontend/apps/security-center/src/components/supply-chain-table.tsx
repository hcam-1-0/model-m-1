import { supplyChainRecords } from "../data/security-projections";
export function SupplyChainTable() {
  return (
    <div className="table-scroll" tabIndex={0}>
      <table>
        <thead>
          <tr>
            <th>Component</th>
            <th>License</th>
            <th>Vulnerability evidence</th>
            <th>Provenance</th>
            <th>Scanner</th>
          </tr>
        </thead>
        <tbody>
          {supplyChainRecords.map((item) => (
            <tr key={item.ref}>
              <td>
                <strong>{item.component}</strong>
                <small>
                  {item.version} · {item.sbomRef}
                </small>
              </td>
              <td>{item.licenseState}</td>
              <td>{item.vulnerabilityState}</td>
              <td>{item.provenanceState}</td>
              <td>
                <span className="status blocked">Not executed</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
