import { Archive, Clock3, FileWarning, Gauge, GitCompareArrows } from "lucide-react";
import {
  evidenceReferences,
  investigationQueue,
  timelinePage,
} from "../data/investigation-projections";
export function WorkloadStrip() {
  const items = [
    [
      Archive,
      "Open investigations",
      String(investigationQueue.items.filter((item) => item.state === "open").length),
      "server ordered",
    ],
    [Clock3, "Timeline records", String(timelinePage.items.length), "record sequence"],
    [FileWarning, "Evidence references", String(evidenceReferences.length), "unresolved"],
    [GitCompareArrows, "Pending impacts", "3", "append-only"],
    [Gauge, "Validation envelope", "200 records", "C1 / C10 / C50"],
  ] as const;
  return (
    <section className="workload-strip" aria-label="Generated investigation workload">
      {items.map(([Icon, label, value, note]) => (
        <div key={label}>
          <Icon size={18} />
          <span>
            {label}
            <small>{note}</small>
          </span>
          <strong>{value}</strong>
        </div>
      ))}
    </section>
  );
}
