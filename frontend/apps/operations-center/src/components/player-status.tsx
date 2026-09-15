import { CircleAlert, CircleCheck, LoaderCircle } from "lucide-react";

export type PlayerState =
  | "idle"
  | "held"
  | "loading"
  | "attached"
  | "paused"
  | "released"
  | "unavailable"
  | "denied"
  | "unsupported"
  | "fallback";
export function PlayerStatus({
  state,
  reason,
}: {
  readonly state: PlayerState;
  readonly reason: string;
}) {
  const Icon =
    state === "attached" || state === "paused"
      ? CircleCheck
      : state === "loading"
        ? LoaderCircle
        : CircleAlert;
  const label =
    state === "attached"
      ? "Generated live session"
      : state === "held"
        ? "Held by admission"
        : state;
  return (
    <span className={`player-status ${state}`} role="status">
      <Icon size={14} />
      <span>{label}</span>
      <small>{reason.replaceAll("_", " ")}</small>
    </span>
  );
}
