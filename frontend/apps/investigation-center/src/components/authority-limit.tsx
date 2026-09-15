import { ShieldAlert } from "lucide-react";
export function AuthorityLimit({ compact = false }: { readonly compact?: boolean }) {
  return (
    <aside
      aria-label="Investigation authority limitations"
      className={compact ? "authority-limit compact" : "authority-limit"}
    >
      <ShieldAlert size={17} />
      <div>
        <strong>Authority boundary</strong>
        <span>
          Generated records are not identity, guilt, authenticity, admissibility, or proof. Source
          and evidence operations are unavailable.
        </span>
      </div>
    </aside>
  );
}
