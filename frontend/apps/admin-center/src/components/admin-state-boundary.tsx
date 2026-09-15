import { LockKeyhole, ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";
export function AdminStateBoundary({
  state = "ready",
  children,
}: {
  readonly state?: "ready" | "partial" | "stale" | "denied";
  readonly children: ReactNode;
}) {
  if (state === "denied")
    return (
      <section className="state-panel denied">
        <LockKeyhole size={20} />
        <div>
          <strong>Access denied</strong>
          <p>Server authority did not grant this generated view.</p>
        </div>
      </section>
    );
  return (
    <>
      {state !== "ready" ? (
        <section className={`state-panel ${state}`} role="status">
          <ShieldAlert size={20} />
          <div>
            <strong>{state === "stale" ? "Projection is stale" : "Projection is partial"}</strong>
            <p>Use the source, freshness, and limitation fields before interpretation.</p>
          </div>
        </section>
      ) : null}
      {children}
    </>
  );
}
export function AdminPageFrame({
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
        <span className="non-effective-badge">
          <LockKeyhole size={15} /> Non-effective
        </span>
      </header>
      {children}
    </>
  );
}
