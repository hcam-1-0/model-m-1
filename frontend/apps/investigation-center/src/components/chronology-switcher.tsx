export function ChronologySwitcher({
  mode,
  onChange,
}: {
  readonly mode: "record" | "event_context";
  readonly onChange: (mode: "record" | "event_context") => void;
}) {
  return (
    <div className="segmented" role="group" aria-label="Chronology display">
      <button type="button" aria-pressed={mode === "record"} onClick={() => onChange("record")}>
        Record sequence
      </button>
      <button
        type="button"
        aria-pressed={mode === "event_context"}
        onClick={() => onChange("event_context")}
      >
        Event-time context
      </button>
    </div>
  );
}
