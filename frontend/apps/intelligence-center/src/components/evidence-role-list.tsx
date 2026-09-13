import type { EvidenceField } from "../../../../packages/intelligence-contracts/src";
export function EvidenceRoleList({ fields }: { readonly fields: readonly EvidenceField[] }) {
  return (
    <ul className="evidence-list">
      {fields.map((field) => (
        <li key={field.field} className={`evidence-${field.role}`}>
          <span>{field.role}</span>
          <div>
            <strong>{field.field}</strong>
            <p>{field.displayValue}</p>
            <small>{field.limitation}</small>
          </div>
        </li>
      ))}
    </ul>
  );
}
