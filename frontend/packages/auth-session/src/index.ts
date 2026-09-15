import { resolveRouteAccess, type AccessDecision } from "@hcam/capabilities";
import {
  parseSessionProjection,
  type RouteManifest,
  type SessionProjection,
} from "@hcam/contracts";

export type SessionState =
  | "idle"
  | "bootstrapping"
  | "ready"
  | "changing_context"
  | "reauthentication"
  | "expired"
  | "revoked"
  | "failure";
export interface SessionSnapshot {
  readonly state: SessionState;
  readonly session: SessionProjection | null;
  readonly generation: number;
}

export class SessionController {
  #snapshot: SessionSnapshot = { state: "idle", session: null, generation: 0 };
  #teardown = new Set<() => void>();
  snapshot(): SessionSnapshot {
    return this.#snapshot;
  }
  registerTeardown(callback: () => void): () => void {
    this.#teardown.add(callback);
    return () => this.#teardown.delete(callback);
  }
  bootstrap(value: unknown): SessionSnapshot {
    const parsed = parseSessionProjection(value);
    this.#snapshot = parsed
      ? {
          state: parsed.reauthenticationRequired ? "reauthentication" : "ready",
          session: parsed,
          generation: this.#snapshot.generation + 1,
        }
      : { state: "failure", session: null, generation: this.#snapshot.generation + 1 };
    return this.#snapshot;
  }
  beginContextChange(): SessionSnapshot {
    for (const callback of this.#teardown) callback();
    this.#snapshot = {
      state: "changing_context",
      session: null,
      generation: this.#snapshot.generation + 1,
    };
    return this.#snapshot;
  }
  revoke(): SessionSnapshot {
    for (const callback of this.#teardown) callback();
    this.#snapshot = { state: "revoked", session: null, generation: this.#snapshot.generation + 1 };
    return this.#snapshot;
  }
  access(route: RouteManifest, now?: Date): AccessDecision {
    return resolveRouteAccess(route, this.#snapshot.session, now);
  }
}

export function validateRequestMetadata(
  origin: string,
  expectedOrigin: string,
  fetchSite: string,
): boolean {
  return origin === expectedOrigin && (fetchSite === "same-origin" || fetchSite === "same-site");
}
