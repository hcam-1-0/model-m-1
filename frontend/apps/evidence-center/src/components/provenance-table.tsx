import type { ProvenanceProjection } from "../../../../packages/investigation-contracts/src";

export function ProvenanceTable({ projection }: { readonly projection: ProvenanceProjection }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Edge</th>
            <th>From</th>
            <th>Relation</th>
            <th>To</th>
          </tr>
        </thead>
        <tbody>
          {projection.edges.map((edge) => (
            <tr key={edge.ref}>
              <td>
                <code>{edge.ref}</code>
              </td>
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
    </div>
  );
}
