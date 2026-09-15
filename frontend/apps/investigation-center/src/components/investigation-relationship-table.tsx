import type { ProvenanceProjection } from "../../../../packages/investigation-contracts/src";
export function InvestigationRelationshipTable({
  projection,
}: {
  readonly projection: ProvenanceProjection;
}) {
  return (
    <div className="relationship-tables">
      <section className="panel">
        <header>
          <h2>Authoritative nodes</h2>
          <span>{projection.nodes.length}</span>
        </header>
        <table>
          <thead>
            <tr>
              <th>Reference</th>
              <th>Label</th>
              <th>Kind</th>
            </tr>
          </thead>
          <tbody>
            {projection.nodes.map((node) => (
              <tr key={node.ref}>
                <td>
                  <code>{node.ref}</code>
                </td>
                <td>{node.label}</td>
                <td>{node.kind}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="panel">
        <header>
          <h2>Authoritative edges</h2>
          <span>{projection.edges.length}</span>
        </header>
        <table>
          <thead>
            <tr>
              <th>From</th>
              <th>Relation</th>
              <th>To</th>
            </tr>
          </thead>
          <tbody>
            {projection.edges.map((edge) => (
              <tr key={edge.ref}>
                <td>
                  <code>{edge.fromRef}</code>
                </td>
                <td>{edge.relation.replaceAll("_", " ")}</td>
                <td>
                  <code>{edge.toRef}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
