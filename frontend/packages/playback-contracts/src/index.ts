import type { ResourceId } from "@hcam/contracts";
export type PlaybackState =
  | "unavailable"
  | "approval_required"
  | "requesting"
  | "negotiating"
  | "ready"
  | "playing"
  | "paused"
  | "stalled"
  | "reconnecting"
  | "fallback"
  | "expiring"
  | "expired"
  | "revoked"
  | "unsupported"
  | "releasing"
  | "released"
  | "denied"
  | "conflict"
  | "scope_transition"
  | "failure";
export interface PlaybackProposal {
  readonly cameraRef: ResourceId;
  readonly reason: string;
  readonly requestedSeconds: number;
}
export interface PlaybackSessionProjection {
  readonly state: PlaybackState;
  readonly sessionRef: string | null;
  readonly expiresAt: string | null;
  readonly locatorExposed: false;
  readonly renewable?: boolean;
  readonly closeable?: boolean;
  readonly revision?: number;
}
export interface PlaybackAdapter {
  propose(input: PlaybackProposal): Promise<PlaybackSessionProjection>;
  close(): void;
}
export function validatePlaybackProposal(value: PlaybackProposal): boolean {
  return (
    value.reason.trim().length >= 8 &&
    value.reason.length <= 512 &&
    value.requestedSeconds >= 5 &&
    value.requestedSeconds <= 300
  );
}
