import { ArrowRight, Ban } from "lucide-react";
import { Link } from "react-router";
import type { EvidenceReference } from "../../../../packages/investigation-contracts/src";

export function EvidenceReferenceTable({
  items,
}: {
  readonly items: readonly EvidenceReference[];
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Reference</th>
            <th>Availability</th>
            <th>Integrity</th>
            <th>Provenance</th>
            <th>Custody</th>
            <th>Access</th>
            <th>
              <span className="sr-only">Open</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.ref}>
              <td>
                <strong>{item.label}</strong>
                <code>{item.ref}</code>
              </td>
              <td>
                <span className={`status-chip status-${item.availability}`}>
                  {item.availability}
                </span>
              </td>
              <td>
                <span className={`status-chip status-${item.integrity}`}>
                  {item.integrity.replaceAll("_", " ")}
                </span>
              </td>
              <td>{item.provenance}</td>
              <td>{item.custody.replaceAll("_", " ")}</td>
              <td>
                {item.access === "denied" ? (
                  <span className="denied">
                    <Ban size={13} /> Denied
                  </span>
                ) : (
                  item.access
                )}
              </td>
              <td>
                <Link
                  className="row-link"
                  to={`/evidence/${item.ref}`}
                  aria-label={`Open ${item.label}`}
                >
                  <ArrowRight size={15} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
