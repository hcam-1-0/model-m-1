import { ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";
export function PlatformOperationsPageFrame({
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
        <span className="platform-badge">
          <ShieldAlert size={15} /> Generated operations
        </span>
      </header>
      {children}
    </>
  );
}
export function PlatformOperationsStateBoundary({
  state,
  children,
}: {
  readonly state: "ready" | "partial" | "stale" | "degraded" | "unknown";
  readonly children: ReactNode;
}) {
  return (
    <>
      {state !== "ready" ? (
        <section className={`platform-state ${state}`} role="status">
          <ShieldAlert size={20} />
          <div>
            <strong>{state} projection</strong>
            <p>
              Check source freshness, completeness, and limitations. This is not live telemetry.
            </p>
          </div>
        </section>
      ) : null}
      {children}
    </>
  );
}
