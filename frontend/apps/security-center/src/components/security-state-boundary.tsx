import { LockKeyhole, ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";
export function SecurityPageFrame({
  eyebrow,
  title,
  description,
  children,
}: {
  readonly eyebrow: string;
  readonly title: string;
  readonly description: string;
  readonly children: ReactNode;
}) {
  return (
    <>
      <header className="page-heading">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <span className="qualified-badge">
          <ShieldAlert size={15} /> Qualified projection
        </span>
      </header>
      {children}
    </>
  );
}
export function SecurityStateBoundary({
  state,
  children,
}: {
  readonly state: "ready" | "partial" | "stale" | "denied";
  readonly children: ReactNode;
}) {
  if (state === "denied")
    return (
      <section className="state-panel denied">
        <LockKeyhole size={20} />
        <div>
          <strong>Access denied</strong>
          <p>Server authority withheld this projection.</p>
        </div>
      </section>
    );
  return (
    <>
      {state !== "ready" ? (
        <section className={`state-panel ${state}`}>
          <ShieldAlert size={20} />
          <div>
            <strong>
              {state === "partial" ? "Partial assurance projection" : "Stale assurance evidence"}
            </strong>
            <p>No absence-of-risk conclusion may be inferred.</p>
          </div>
        </section>
      ) : null}
      {children}
    </>
  );
}
