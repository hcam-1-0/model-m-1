import { toSafeProblem, type ProblemDetails } from "@hcam/contracts";
import createClient from "openapi-fetch";
import type { SessionProjection } from "@hcam/contracts";

export interface GeneratedPaths {
  readonly "/api/session": {
    readonly get: {
      readonly responses: {
        readonly 200: { readonly content: { readonly "application/json": SessionProjection } };
      };
    };
  };
}
export function createGeneratedSameOriginClient() {
  return createClient<GeneratedPaths>({
    baseUrl: "",
    credentials: "same-origin",
    redirect: "error",
    cache: "no-store",
  });
}

export interface OperationContract<T> {
  readonly operationId: string;
  readonly method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  readonly path: `/${string}`;
  readonly timeoutMs: number;
  readonly maxResponseBytes: number;
  readonly command: boolean;
  readonly requiresReason: boolean;
  readonly requiresEtag: boolean;
  readonly requiresIdempotency: boolean;
  readonly parse: (value: unknown) => T | null;
}
export type TransportResult<T> =
  | { readonly ok: true; readonly data: T; readonly etag: string | null }
  | { readonly ok: false; readonly problem: ProblemDetails };
export interface RequestContext {
  readonly csrfToken?: string;
  readonly reason?: string;
  readonly etag?: string;
  readonly idempotencyKey?: string;
  readonly signal?: AbortSignal;
}

function ensureSameOriginPath(path: string): void {
  if (!path.startsWith("/") || path.startsWith("//") || path.includes("\\") || path.includes(".."))
    throw new Error("unsafe_operation_path");
}

export async function executeOperation<T>(
  contract: OperationContract<T>,
  context: RequestContext = {},
): Promise<TransportResult<T>> {
  ensureSameOriginPath(contract.path);
  if (contract.requiresReason && !context.reason?.trim())
    return { ok: false, problem: toSafeProblem(400, { code: "invalid" }) };
  if (contract.requiresEtag && !context.etag)
    return { ok: false, problem: toSafeProblem(409, { code: "conflict" }) };
  if (contract.requiresIdempotency && !context.idempotencyKey)
    return { ok: false, problem: toSafeProblem(400, { code: "invalid" }) };
  const timeout = AbortSignal.timeout(Math.min(Math.max(contract.timeoutMs, 250), 30_000));
  const signal = context.signal ? AbortSignal.any([context.signal, timeout]) : timeout;
  const headers = new Headers({ Accept: "application/json" });
  if (context.csrfToken) headers.set("X-CSRF-Token", context.csrfToken);
  if (context.reason) headers.set("X-HCAM-Reason", context.reason.slice(0, 512));
  if (context.etag) headers.set("If-Match", context.etag);
  if (context.idempotencyKey) headers.set("Idempotency-Key", context.idempotencyKey);
  try {
    const response = await fetch(contract.path, {
      method: contract.method,
      headers,
      credentials: "same-origin",
      redirect: "error",
      cache: "no-store",
      signal,
    });
    const body = await response.text();
    if (new TextEncoder().encode(body).byteLength > contract.maxResponseBytes)
      return { ok: false, problem: toSafeProblem(502, { code: "incompatible" }) };
    let decoded: unknown = null;
    try {
      decoded = body ? JSON.parse(body) : null;
    } catch {
      return { ok: false, problem: toSafeProblem(response.status, { code: "incompatible" }) };
    }
    if (!response.ok) return { ok: false, problem: toSafeProblem(response.status, decoded) };
    const parsed = contract.parse(decoded);
    return parsed === null
      ? { ok: false, problem: toSafeProblem(502, { code: "incompatible" }) }
      : { ok: true, data: parsed, etag: response.headers.get("ETag") };
  } catch (error) {
    return {
      ok: false,
      problem: toSafeProblem(0, {
        code:
          error instanceof DOMException && error.name === "TimeoutError" ? "timeout" : "offline",
      }),
    };
  }
}

export function generatedIntelligenceOperation<T>(
  operationId: string,
  path: `/${string}`,
  parse: (value: unknown) => T | null,
  command = false,
): OperationContract<T> {
  if (!operationId.startsWith("generated") || !path.startsWith("/api/intelligence/"))
    throw new Error("invalid_generated_intelligence_operation");
  return Object.freeze({
    operationId,
    method: command ? "POST" : "GET",
    path,
    timeoutMs: 10_000,
    maxResponseBytes: 1_048_576,
    command,
    requiresReason: command,
    requiresEtag: command,
    requiresIdempotency: command,
    parse,
  });
}

export function generatedInvestigationOperation<T>(
  operationId: string,
  path: `/${string}`,
  parse: (value: unknown) => T | null,
  command = false,
): OperationContract<T> {
  if (
    !operationId.startsWith("generated") ||
    (!path.startsWith("/api/investigations/") && !path.startsWith("/api/evidence/"))
  )
    throw new Error("invalid_generated_investigation_operation");
  return Object.freeze({
    operationId,
    method: command ? "POST" : "GET",
    path,
    timeoutMs: 10_000,
    maxResponseBytes: 1_048_576,
    command,
    requiresReason: command,
    requiresEtag: command,
    requiresIdempotency: command,
    parse,
  });
}

export function generatedAdministrationOperation<T>(
  operationId: string,
  path: `/${string}`,
  parse: (value: unknown) => T | null,
  command = false,
): OperationContract<T> {
  const validPath =
    path.startsWith("/api/admin/") ||
    path.startsWith("/api/security/") ||
    path.startsWith("/api/operations/platform/");
  if (!operationId.startsWith("generated") || !validPath)
    throw new Error("invalid_generated_administration_operation");
  return Object.freeze({
    operationId,
    method: command ? "POST" : "GET",
    path,
    timeoutMs: 10_000,
    maxResponseBytes: 1_048_576,
    command,
    requiresReason: command,
    requiresEtag: command,
    requiresIdempotency: command,
    parse,
  });
}
