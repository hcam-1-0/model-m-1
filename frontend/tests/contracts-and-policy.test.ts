import { describe, expect, it } from "vitest";
import {
  asResourceId,
  parseSessionProjection,
  parseWorkspaceWindowIntent,
  toSafeProblem,
} from "@hcam/contracts";
import {
  intersectCapabilities,
  resolveResourceProfile,
  resolveRouteAccess,
} from "@hcam/capabilities";
import { classifyEvent } from "@hcam/event-invalidation";
import { validateViewport } from "@hcam/gis-contracts";
import {
  baseMessages,
  catalogues,
  hasCompleteCatalogue,
  loadDisplayPreferences,
  parseDisplayPreferences,
  saveDisplayPreferences,
} from "@hcam/i18n";
import { portals, routeByPath, routes, safeRouteHref, visiblePortals } from "@hcam/navigation";
import { disabledSignalAdapter, validateSignal } from "@hcam/observability";
import { validatePlaybackProposal } from "@hcam/playback-contracts";
import {
  createBoundedQueryClient,
  defineQueryPolicy,
  queryKey,
  shouldRetry,
  toQueryDefaults,
} from "@hcam/query-policy";
import { designTokenVersion, densityScale } from "@hcam/design-tokens";
import {
  generatedEvent,
  generatedMarker,
  generatedSession,
  generatedStates,
} from "@hcam/test-fixtures";
import { generatedOnlyNotice } from "@hcam/test-support";

describe("foundation contracts", () => {
  it("accepts only strict generated sessions", () => {
    const session = generatedSession();
    expect(parseSessionProjection(session)).toEqual(session);
    expect(parseSessionProjection({ ...session, unknown: true })).toBeNull();
    expect(parseSessionProjection({ ...session, csrfToken: "short" })).toBeNull();
    expect(parseSessionProjection(null)).toBeNull();
  });
  it("minimizes problems and resource references", () => {
    expect(toSafeProblem(403, null).code).toBe("denied");
    expect(
      toSafeProblem(409, {
        code: "conflict",
        detail: "discard me",
        correlation_ref: "CORR_00000001",
      }),
    ).toEqual({
      type: "about:blank",
      title: "Request could not be completed",
      status: 409,
      code: "conflict",
      correlationRef: "CORR_00000001",
    });
    expect(
      toSafeProblem(500, { code: "raw_server_error", correlation_ref: "bad value" }).code,
    ).toBe("safe_failure");
    expect(asResourceId("SYN_REF_0001")).toBe("SYN_REF_0001");
    expect(asResourceId("unsafe value")).toBeNull();
    expect(
      parseWorkspaceWindowIntent({ version: 1, portal: "operations", view: "list" }),
    ).toMatchObject({ portal: "operations" });
    expect(
      parseWorkspaceWindowIntent({
        version: 1,
        portal: "operations",
        view: "detail",
        opaqueResourceRef: "unsafe value",
      }),
    ).toBeNull();
    expect(parseWorkspaceWindowIntent(null)).toBeNull();
  });
});

describe("capability and route policy", () => {
  it("fails closed for unknown, missing, stale, reauthentication, and missing capability", () => {
    const route = routes[0]!;
    const session = generatedSession();
    expect(resolveRouteAccess(undefined, session).reason).toBe("route_unknown");
    expect(resolveRouteAccess(route, null).reason).toBe("session_missing");
    expect(resolveRouteAccess(route, { ...session, reauthenticationRequired: true }).reason).toBe(
      "reauthentication_required",
    );
    expect(resolveRouteAccess(route, session, new Date("2026-09-06T12:00:00.000Z")).reason).toBe(
      "session_stale",
    );
    expect(
      resolveRouteAccess(
        route,
        { ...session, capabilities: ["operations.viewer"] },
        new Date("2026-09-06T10:30:00.000Z"),
      ).reason,
    ).toBe("capability_missing");
    expect(resolveRouteAccess(route, session, new Date("2026-09-06T10:30:00.000Z")).allowed).toBe(
      true,
    );
    expect(
      intersectCapabilities(["command.viewer", "security.viewer"], ["command.viewer"]),
    ).toEqual(["command.viewer"]);
    expect(visiblePortals(session, new Date("2026-09-06T10:30:00.000Z"))).toHaveLength(7);
  });
  it("resolves bounded profiles without expanding authority", () => {
    const common = {
      requested: "control_room",
      serverCeiling: "control_room",
      buildSupported: ["low_resource", "enhanced", "control_room"],
      coarseBrowserSupport: "enhanced",
      sessionHealth: "healthy",
    } as const;
    expect(resolveResourceProfile(common)).toMatchObject({
      profile: "control_room",
      reason: "requested",
    });
    expect(resolveResourceProfile({ ...common, sessionHealth: "degraded" })).toMatchObject({
      profile: "low_resource",
      reason: "session_health",
    });
    expect(resolveResourceProfile({ ...common, serverCeiling: "enhanced" })).toMatchObject({
      profile: "enhanced",
      reason: "server_limit",
    });
    expect(resolveResourceProfile({ ...common, coarseBrowserSupport: "basic" })).toMatchObject({
      profile: "low_resource",
      reason: "browser_limit",
    });
    expect(resolveResourceProfile({ ...common, buildSupported: ["low_resource"] })).toMatchObject({
      profile: "low_resource",
      reason: "build_limit",
    });
  });
  it("keeps URLs allowlisted and opaque", () => {
    expect(routeByPath("/command")?.portalId).toBe("command");
    expect(routeByPath("/unknown")).toBeUndefined();
    expect(
      safeRouteHref(routes[0]!, { window: "secondary_1", secret: "blocked", page: "bad value" }),
    ).toBe("/command?window=secondary_1");
    expect(portals).toHaveLength(7);
  });
});

describe("state, event, and adapter policy", () => {
  it("classifies event ordering and scope", () => {
    expect(classifyEvent(generatedEvent(1), "SYN-DEPT-01", 0).disposition).toBe("accepted");
    expect(classifyEvent(generatedEvent(2), "SYN-DEPT-01", 2).disposition).toBe("duplicate");
    expect(classifyEvent(generatedEvent(1), "SYN-DEPT-01", 2).disposition).toBe("reordered");
    expect(classifyEvent(generatedEvent(4), "SYN-DEPT-01", 2).disposition).toBe("gap");
    expect(
      classifyEvent({ ...generatedEvent(3), departmentRef: "SYN-OTHER" }, "SYN-DEPT-01", 2)
        .disposition,
    ).toBe("wrong_department");
    expect(
      classifyEvent({ ...generatedEvent(3), version: "2.0.0" }, "SYN-DEPT-01", 2).disposition,
    ).toBe("unknown_version");
  });
  it("validates renderer-neutral GIS and approval-gated playback", () => {
    expect(validateViewport({ west: 68, south: 20, east: 75, north: 24, zoom: 8 })).toBe(true);
    expect(validateViewport({ west: 180, south: 20, east: 75, north: 24, zoom: 8 })).toBe(false);
    expect(
      validatePlaybackProposal({
        cameraRef: asResourceId("SYN_CAM_0001")!,
        reason: "Generated review reason",
        requestedSeconds: 30,
      }),
    ).toBe(true);
    expect(
      validatePlaybackProposal({
        cameraRef: asResourceId("SYN_CAM_0001")!,
        reason: "short",
        requestedSeconds: 500,
      }),
    ).toBe(false);
  });
  it("enforces nonpersistent query policy and command retry denial", () => {
    const read = defineQueryPolicy({
      operationId: "generated.read",
      queryClass: "summary",
      staleMs: 1000,
      cacheMs: 2000,
      retryLimit: 2,
      pollMs: 5000,
      persist: false,
    });
    expect(shouldRetry(read, 0, "offline")).toBe(true);
    expect(shouldRetry(read, 0, "denied")).toBe(false);
    expect(shouldRetry(read, 2, "offline")).toBe(false);
    expect(queryKey("v1", "SYN-DEPT-01", "generated.read", "SYN_REF_01")).toHaveLength(4);
    expect(queryKey("v1", "SYN-DEPT-01", "generated.read")).toHaveLength(3);
    expect(toQueryDefaults(read)).toMatchObject({
      staleTime: 1000,
      gcTime: 2000,
      refetchInterval: 5000,
      networkMode: "online",
    });
    expect(toQueryDefaults({ ...read, pollMs: null }).refetchInterval).toBe(false);
    expect(toQueryDefaults(read).retry(0, { code: "offline" })).toBe(true);
    const client = createBoundedQueryClient();
    expect(client.getDefaultOptions().mutations?.retry).toBe(false);
    client.clear();
    expect(() => defineQueryPolicy({ ...read, queryClass: "command", retryLimit: 1 })).toThrow(
      "commands_cannot_retry",
    );
    expect(() => defineQueryPolicy({ ...read, retryLimit: 3 })).toThrow("invalid_query_policy");
  });
});

describe("localization, telemetry, and generated fixtures", () => {
  it("has complete three-locale and pseudo-locale catalogues", () => {
    expect(Object.keys(baseMessages).length).toBeGreaterThan(30);
    expect(hasCompleteCatalogue("en")).toBe(true);
    expect(hasCompleteCatalogue("gu")).toBe(true);
    expect(hasCompleteCatalogue("hi")).toBe(true);
    expect(hasCompleteCatalogue("en-XA")).toBe(true);
    expect(catalogues.gu["portal.command"]).not.toBe(baseMessages["portal.command"]);
  });
  it("accepts only harmless unexpired preferences", () => {
    const preference = {
      version: 1,
      theme: "dark",
      density: "compact",
      locale: "gu",
      reducedMotion: true,
      expiresAt: "2027-01-01T00:00:00.000Z",
    } as const;
    expect(parseDisplayPreferences(preference, new Date("2026-09-06T00:00:00.000Z"))).toEqual(
      preference,
    );
    expect(parseDisplayPreferences({ ...preference, locale: "xx" })).toBeNull();
    expect(parseDisplayPreferences(preference, new Date("2028-01-01T00:00:00.000Z"))).toBeNull();
    expect(parseDisplayPreferences(null)).toBeNull();
    saveDisplayPreferences(localStorage, preference);
    expect(loadDisplayPreferences(localStorage, new Date("2026-09-06T00:00:00.000Z"))).toEqual(
      preference,
    );
    localStorage.setItem("hcam.display.v1", "not-json");
    expect(loadDisplayPreferences(localStorage)).toBeNull();
    localStorage.setItem("hcam.display.v1", "x".repeat(2049));
    expect(loadDisplayPreferences(localStorage)).toBeNull();
    expect(loadDisplayPreferences(localStorage)).toBeNull();
  });
  it("allows only bounded low-cardinality signals", () => {
    const signal = {
      name: "route_view",
      portal: "command",
      routeClass: "overview",
      state: "ready",
      outcome: "ok",
      durationBucket: "lt100",
    } as const;
    expect(validateSignal(signal)).toBe(true);
    expect(validateSignal({ ...signal, routeClass: "x".repeat(65) })).toBe(false);
    expect(disabledSignalAdapter.enabled).toBe(false);
    disabledSignalAdapter.emit(signal);
    disabledSignalAdapter.shutdown();
  });
  it("marks every fixture as generated and non-operational", () => {
    expect(generatedMarker).toContain("GENERATED");
    expect(generatedStates).toHaveLength(12);
    expect(generatedOnlyNotice).toContain("Not for operational use");
    expect(designTokenVersion).toBe("hcam.tokens.v1");
    expect(densityScale.compact).toBeLessThan(densityScale.spacious);
  });
});
