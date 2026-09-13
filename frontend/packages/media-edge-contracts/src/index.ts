export type PlaybackTransport = "hls" | "native_hls" | "whep";
export type PlaybackRendition = "low" | "medium" | "high";
export interface PlaybackSessionRequest {
  readonly streamRef: string;
  readonly departmentRef: string;
  readonly purpose: "live_view";
  readonly transportPreference: readonly PlaybackTransport[];
  readonly renditionCeiling: PlaybackRendition;
  readonly reason: string;
}
export interface PlaybackSessionGrant {
  readonly sessionRef: string;
  readonly streamRef: string;
  readonly transport: PlaybackTransport;
  readonly rendition: PlaybackRendition;
  readonly mediaPath: string;
  readonly grant: string;
  readonly issuedAt: string;
  readonly expiresAt: string;
  readonly sourceRevision: string;
  readonly generated: true;
}
const reference = /^SYN-[A-Z0-9-]{3,48}$/u;
const opaqueGrant = /^g1_[A-Za-z0-9_-]{24,96}$/u;
const allowedPath = /^\/media-edge\/sessions\/SYN-[A-Z0-9-]{3,48}\/(?:master\.m3u8|whep)$/u;
const allowedResourcePath =
  /^\/media-edge\/sessions\/SYN-[A-Z0-9-]{3,48}\/(?:master\.m3u8|init\.mp4|segment-[0-9]{1,4}\.(?:m4s|ts)|whep)$/u;
const allowedTransports: ReadonlySet<unknown> = new Set<PlaybackTransport>([
  "hls",
  "native_hls",
  "whep",
]);
const allowedRenditions: ReadonlySet<unknown> = new Set<PlaybackRendition>([
  "low",
  "medium",
  "high",
]);
export function validateSessionRequest(value: unknown): value is PlaybackSessionRequest {
  if (!value || typeof value !== "object") return false;
  const request = value as Partial<PlaybackSessionRequest>;
  return (
    typeof request.streamRef === "string" &&
    reference.test(request.streamRef) &&
    typeof request.departmentRef === "string" &&
    reference.test(request.departmentRef) &&
    request.purpose === "live_view" &&
    Array.isArray(request.transportPreference) &&
    request.transportPreference.length > 0 &&
    request.transportPreference.length <= 3 &&
    request.transportPreference.every((transport) => allowedTransports.has(transport)) &&
    typeof request.renditionCeiling === "string" &&
    allowedRenditions.has(request.renditionCeiling) &&
    typeof request.reason === "string" &&
    request.reason.length >= 8 &&
    request.reason.length <= 240
  );
}
export function validatePlaybackGrant(value: unknown, now: Date): value is PlaybackSessionGrant {
  if (!value || typeof value !== "object") return false;
  const grant = value as Partial<PlaybackSessionGrant>;
  if (typeof grant.issuedAt !== "string" || typeof grant.expiresAt !== "string") return false;
  const issued = Date.parse(grant.issuedAt);
  const expires = Date.parse(grant.expiresAt);
  return (
    Boolean(grant.generated) &&
    typeof grant.sessionRef === "string" &&
    reference.test(grant.sessionRef) &&
    typeof grant.streamRef === "string" &&
    reference.test(grant.streamRef) &&
    typeof grant.grant === "string" &&
    opaqueGrant.test(grant.grant) &&
    typeof grant.mediaPath === "string" &&
    allowedPath.test(grant.mediaPath) &&
    !/[?#]/u.test(grant.mediaPath) &&
    Number.isFinite(issued) &&
    Number.isFinite(expires) &&
    issued <= now.getTime() &&
    expires > now.getTime() &&
    expires - issued <= 120_000
  );
}
export function isSafeMediaDestination(path: string, origin: string): boolean {
  if (!path.startsWith("/") || path.startsWith("//") || /[?#]/u.test(path)) return false;
  try {
    const target = new URL(path, origin);
    return (
      target.origin === origin &&
      allowedPath.test(target.pathname) &&
      !target.username &&
      !target.password
    );
  } catch {
    return false;
  }
}
export function isSafeMediaResourceDestination(path: string, origin: string): boolean {
  try {
    const target = new URL(path, origin);
    return (
      target.origin === origin &&
      allowedResourcePath.test(target.pathname) &&
      !target.username &&
      !target.password &&
      !target.search &&
      !target.hash
    );
  } catch {
    return false;
  }
}
export function authorizationHeaders(
  grant: PlaybackSessionGrant,
): Readonly<Record<string, string>> {
  return Object.freeze({ Authorization: `HCAM-Grant ${grant.grant}` });
}

export const playbackLifecycleStates = [
  "idle",
  "admission_pending",
  "reason_required",
  "requesting",
  "negotiating",
  "loading",
  "playing",
  "paused",
  "stalled",
  "reconnecting",
  "fallback",
  "expiring",
  "expired",
  "revoked",
  "unsupported",
  "failed",
  "releasing",
  "released",
  "denied",
  "conflict",
  "scope_transition",
] as const;
export type PlaybackLifecycleState = (typeof playbackLifecycleStates)[number];
export interface PlaybackLease {
  readonly sessionRef: string;
  readonly state: PlaybackLifecycleState;
  readonly revision: number;
  readonly expiresAt: string;
  readonly renewalCount: number;
  readonly closedAt: string | null;
}
const transitions: Readonly<Record<PlaybackLifecycleState, readonly PlaybackLifecycleState[]>> = {
  idle: ["admission_pending"],
  admission_pending: ["reason_required", "requesting", "denied"],
  reason_required: ["requesting", "denied"],
  requesting: ["negotiating", "loading", "denied", "failed"],
  negotiating: ["playing", "fallback", "failed", "releasing"],
  loading: ["playing", "stalled", "failed", "releasing"],
  playing: ["paused", "stalled", "expiring", "revoked", "scope_transition", "releasing"],
  paused: ["playing", "expiring", "revoked", "scope_transition", "releasing"],
  stalled: ["reconnecting", "fallback", "failed", "releasing"],
  reconnecting: ["loading", "fallback", "failed", "releasing"],
  fallback: ["loading", "failed", "releasing"],
  expiring: ["playing", "expired", "releasing"],
  expired: ["releasing", "released"],
  revoked: ["releasing", "released"],
  unsupported: ["releasing", "released"],
  failed: ["releasing", "released"],
  denied: ["released"],
  conflict: ["releasing", "released"],
  scope_transition: ["releasing", "released"],
  releasing: ["released"],
  released: ["released"],
};
export function transitionPlayback(
  lease: PlaybackLease,
  next: PlaybackLifecycleState,
  now: Date,
): PlaybackLease {
  if (!transitions[lease.state].includes(next)) throw new Error("invalid_playback_transition");
  if (lease.state === "released" && next === "released") return lease;
  return {
    ...lease,
    state: next,
    revision: lease.revision + 1,
    closedAt: next === "released" ? now.toISOString() : lease.closedAt,
  };
}
export function renewPlayback(
  lease: PlaybackLease,
  now: Date,
  extensionMs = 60_000,
): PlaybackLease {
  if (
    !["playing", "paused", "expiring"].includes(lease.state) ||
    lease.renewalCount >= 1 ||
    extensionMs < 10_000 ||
    extensionMs > 60_000
  )
    throw new Error("playback_renewal_denied");
  return {
    ...lease,
    state: "playing",
    revision: lease.revision + 1,
    expiresAt: new Date(now.getTime() + extensionMs).toISOString(),
    renewalCount: lease.renewalCount + 1,
  };
}
