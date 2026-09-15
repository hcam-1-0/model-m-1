import { ShieldAlert, ShieldCheck } from "lucide-react";
import type { AuthorityClass } from "../../../../packages/intelligence-contracts/src";
export function AuthorityBadge({ authority }: { readonly authority: AuthorityClass }) {
  const human = authority === "human_decision";
  return (
    <span className={`authority authority-${authority}`}>
      {human ? <ShieldCheck size={13} /> : <ShieldAlert size={13} />}
      {authority.replaceAll("_", " ")}
    </span>
  );
}
