export type MediaSignalName =
  | "session_started"
  | "manifest_loaded"
  | "playing"
  | "stalled"
  | "fallback"
  | "recovering"
  | "teardown";
export interface MediaSignal {
  readonly name: MediaSignalName;
  readonly transport: "hls" | "native_hls" | "whep" | "none";
  readonly reason: string;
  readonly durationBand: "none" | "under_1s" | "1_to_5s" | "over_5s";
}
export type SignalSink = (signal: MediaSignal) => void;
export const discardMediaSignal: SignalSink = () => undefined;
export function durationBand(milliseconds: number): MediaSignal["durationBand"] {
  if (!Number.isFinite(milliseconds) || milliseconds <= 0) return "none";
  if (milliseconds < 1_000) return "under_1s";
  return milliseconds <= 5_000 ? "1_to_5s" : "over_5s";
}
