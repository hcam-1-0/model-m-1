import { Activity, CircleCheck, CircleX, Clock3 } from "lucide-react";
import type { StreamProjection } from "@hcam/camera-live-domain";

export function DiagnosticsTimeline({ stream }: { readonly stream: StreamProjection }) {
  const successful = stream.probe.state === "succeeded";
  const events = [
    {
      time: "09:02",
      label: "Catalogue projection loaded",
      detail: "Generated source revision accepted",
      ok: true,
    },
    {
      time: "09:01",
      label: successful ? "Metadata probe completed" : "Metadata probe unavailable",
      detail: successful
        ? `${stream.probe.latencyMs} ms latency band`
        : "No connection attempt performed",
      ok: successful,
    },
    {
      time: "09:00",
      label: "Capability snapshot evaluated",
      detail: `${stream.capabilities.status} inventory; ${stream.capabilities.profileCount ?? 0} profiles`,
      ok: stream.capabilities.status === "fresh",
    },
  ];
  return (
    <section className="detail-panel diagnostics" aria-labelledby="diagnostics-title">
      <header>
        <div>
          <span className="eyebrow">SAFE DIAGNOSTICS</span>
          <h2 id="diagnostics-title">Generated timeline</h2>
        </div>
        <Activity size={18} />
      </header>
      <ol>
        {events.map((event) => (
          <li key={`${event.time}-${event.label}`}>
            <time>
              <Clock3 size={13} /> {event.time}
            </time>
            {event.ok ? (
              <CircleCheck className="ok" size={17} />
            ) : (
              <CircleX className="bad" size={17} />
            )}
            <div>
              <strong>{event.label}</strong>
              <p>{event.detail}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
