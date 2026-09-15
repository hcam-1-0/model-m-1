import { Activity, AlertTriangle, CheckCheck, Clock3 } from "lucide-react";
export function WorkloadStrip({
  values = [10, 7, 2, 26],
}: {
  readonly values?: readonly number[];
}) {
  const entries = [
    ["Open queues", values[0], Activity],
    ["Awaiting review", values[1], Clock3],
    ["Correction holds", values[2], AlertTriangle],
    ["Blocked producers", values[3], CheckCheck],
  ] as const;
  return (
    <section className="workload-strip" aria-label="Intelligence workload">
      {entries.map(([label, value, Icon]) => (
        <div key={label}>
          <Icon size={17} />
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </section>
  );
}
