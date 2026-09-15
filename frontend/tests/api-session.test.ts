import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createGeneratedSameOriginClient,
  executeOperation,
  type OperationContract,
} from "@hcam/api-client";
import { SessionController, validateRequestMetadata } from "@hcam/auth-session";
import { generatedSession } from "@hcam/test-fixtures";
import { routes } from "@hcam/navigation";

const contract: OperationContract<{ readonly value: string }> = {
  operationId: "generated.read",
  method: "GET",
  path: "/api/generated",
  timeoutMs: 1000,
  maxResponseBytes: 1024,
  command: false,
  requiresReason: false,
  requiresEtag: false,
  requiresIdempotency: false,
  parse: (value) =>
    value && typeof value === "object" && (value as Record<string, unknown>).value === "safe"
      ? { value: "safe" }
      : null,
};
afterEach(() => vi.unstubAllGlobals());

describe("same-origin transport", () => {
  it("creates only the generated typed same-origin OpenAPI client", () => {
    expect(createGeneratedSameOriginClient()).toHaveProperty("GET");
  });
  it("returns validated response and ETag", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ value: "safe" }), {
          status: 200,
          headers: { ETag: '"rev-1"' },
        }),
      ),
    );
    await expect(executeOperation(contract)).resolves.toEqual({
      ok: true,
      data: { value: "safe" },
      etag: '"rev-1"',
    });
    expect(fetch).toHaveBeenCalledWith(
      "/api/generated",
      expect.objectContaining({ credentials: "same-origin", redirect: "error", cache: "no-store" }),
    );
  });
  it("minimizes server problems, malformed JSON, invalid schemas, oversized data, and offline errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ code: "denied", detail: "discard" }), { status: 403 }),
        )
        .mockResolvedValueOnce(new Response("not-json", { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify({ unexpected: true }), { status: 200 }))
        .mockResolvedValueOnce(
          new Response(JSON.stringify({ value: "x".repeat(2048) }), { status: 200 }),
        )
        .mockRejectedValueOnce(new TypeError("private raw failure")),
    );
    expect((await executeOperation(contract)).ok).toBe(false);
    expect((await executeOperation(contract)).ok).toBe(false);
    expect((await executeOperation(contract)).ok).toBe(false);
    expect((await executeOperation(contract)).ok).toBe(false);
    const offline = await executeOperation(contract);
    expect(offline).toMatchObject({ ok: false, problem: { code: "offline" } });
    expect(JSON.stringify(offline)).not.toContain("private raw failure");
  });
  it("requires command control headers before dispatch", async () => {
    const command = {
      ...contract,
      method: "POST",
      command: true,
      requiresReason: true,
      requiresEtag: true,
      requiresIdempotency: true,
    } as const;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ value: "safe" }))),
    );
    expect(await executeOperation(command)).toMatchObject({
      ok: false,
      problem: { code: "invalid" },
    });
    expect(await executeOperation(command, { reason: "Generated bounded reason" })).toMatchObject({
      ok: false,
      problem: { code: "conflict" },
    });
    expect(
      await executeOperation(command, { reason: "Generated bounded reason", etag: '"r1"' }),
    ).toMatchObject({ ok: false, problem: { code: "invalid" } });
    expect(
      await executeOperation(command, {
        reason: "Generated bounded reason",
        etag: '"r1"',
        idempotencyKey: "SYN-IDEMPOTENCY-01",
        csrfToken: "SYN-CSRF-00000001",
      }),
    ).toMatchObject({ ok: true });
  });
  it("rejects an unsafe destination before fetch", async () => {
    await expect(executeOperation({ ...contract, path: "//outside.example/path" })).rejects.toThrow(
      "unsafe_operation_path",
    );
  });
});

describe("session controller", () => {
  it("bootstraps, checks access, tears down, changes context, and revokes", () => {
    const controller = new SessionController();
    const teardown = vi.fn();
    const unregister = controller.registerTeardown(teardown);
    expect(controller.snapshot().state).toBe("idle");
    expect(controller.bootstrap(generatedSession()).state).toBe("ready");
    expect(controller.access(routes[0]!, new Date("2026-09-06T10:30:00.000Z")).allowed).toBe(true);
    expect(controller.beginContextChange().state).toBe("changing_context");
    expect(teardown).toHaveBeenCalledTimes(1);
    expect(controller.bootstrap({ invalid: true }).state).toBe("failure");
    expect(
      controller.bootstrap({ ...generatedSession(), reauthenticationRequired: true }).state,
    ).toBe("reauthentication");
    expect(controller.revoke().state).toBe("revoked");
    expect(teardown).toHaveBeenCalledTimes(2);
    unregister();
  });
  it("validates Origin and Fetch Metadata together", () => {
    expect(validateRequestMetadata("https://hcam.local", "https://hcam.local", "same-origin")).toBe(
      true,
    );
    expect(validateRequestMetadata("https://hcam.local", "https://hcam.local", "same-site")).toBe(
      true,
    );
    expect(
      validateRequestMetadata("https://outside.test", "https://hcam.local", "cross-site"),
    ).toBe(false);
  });
});
