import { ShieldAlert } from "lucide-react";

export function EvidenceLimitations({ limitations }: { readonly limitations: readonly string[] }) {
  return (
    <aside aria-label="Evidence authority limitations" className="authority-limit">
      <ShieldAlert size={18} />
      <div>
        <strong>Evidence boundary</strong>
        <span>
          Integrity is not truth, authenticity, identity, guilt, legal admissibility, or proof.
        </span>
        {limitations.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </aside>
  );
}
