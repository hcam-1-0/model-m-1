import type { RelationshipProjection } from "../../intelligence-contracts/src";
export function RelationshipTableRenderer({
  projection,
}: {
  readonly projection: RelationshipProjection;
}) {
  return (
    <div className="relationship-tables">
      <table>
        <caption>Relationship nodes</caption>
        <thead>
          <tr>
            <th>Node</th>
            <th>Type</th>
            <th>State</th>
          </tr>
        </thead>
        <tbody>
          {projection.nodes.map((node) => (
            <tr key={node.ref}>
              <td>
                {node.label}
                <small>{node.ref}</small>
              </td>
              <td>{node.kind}</td>
              <td>{node.state}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <table>
        <caption>Relationship edges</caption>
        <thead>
          <tr>
            <th>From</th>
            <th>Relationship</th>
            <th>To</th>
            <th>Confidence</th>
          </tr>
        </thead>
        <tbody>
          {projection.edges.map((edge) => (
            <tr key={edge.ref}>
              <td>{edge.fromRef}</td>
              <td>{edge.relationship}</td>
              <td>{edge.toRef}</td>
              <td>{edge.confidenceBand}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
