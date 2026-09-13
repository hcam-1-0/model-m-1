import { beforeEach, describe, expect, it, vi } from "vitest";

interface MockHlsInstance {
  readonly config: { xhrSetup: (xhr: XMLHttpRequest, url: string) => void };
  readonly handlers: Map<string, (...args: unknown[]) => void>;
  readonly loadSource: ReturnType<typeof vi.fn>;
  readonly stopLoad: ReturnType<typeof vi.fn>;
  readonly destroy: ReturnType<typeof vi.fn>;
  readonly recoverMediaError: ReturnType<typeof vi.fn>;
}
const hlsMock = vi.hoisted(() => ({ instances: [] as MockHlsInstance[], supported: true }));
vi.mock("hls.js", () => ({
  default: class FakeHls {
    static isSupported = () => hlsMock.supported;
    readonly handlers = new Map<string, (...args: unknown[]) => void>();
    readonly attachMedia = vi.fn();
    readonly loadSource = vi.fn();
    readonly stopLoad = vi.fn();
    readonly detachMedia = vi.fn();
    readonly destroy = vi.fn();
    readonly recoverMediaError = vi.fn();
    constructor(readonly config: { xhrSetup: (xhr: XMLHttpRequest, url: string) => void }) {
      hlsMock.instances.push(this);
    }
    once(event: string, handler: (...args: unknown[]) => void) {
      this.handlers.set(event, handler);
    }
    on(event: string, handler: (...args: unknown[]) => void) {
      this.handlers.set(event, handler);
    }
  },
  ErrorTypes: { MEDIA_ERROR: "mediaError" },
  Events: { MEDIA_ATTACHED: "mediaAttached", MANIFEST_PARSED: "manifestParsed", ERROR: "error" },
}));
import { createHlsAdapter } from "@hcam/media-adapters";
import { generatedPlaybackGrant } from "@hcam/test-fixtures";

const now = () => new Date("2026-09-08T09:00:30.000Z");
const video = () =>
  ({
    pause: vi.fn(),
    removeAttribute: vi.fn(),
    load: vi.fn(),
    play: vi.fn(),
  }) as unknown as HTMLVideoElement;
describe("HLS adapter", () => {
  beforeEach(() => {
    hlsMock.instances.splice(0);
    hlsMock.supported = true;
  });
  it("attaches a valid same-origin generated grant and releases every resource", async () => {
    const signals: unknown[] = [];
    const adapter = createHlsAdapter(generatedPlaybackGrant(), {
      now,
      origin: "http://127.0.0.1:4173",
      signal: (signal) => signals.push(signal),
    });
    expect(await adapter.attach(video())).toEqual({ state: "attached", reason: "ready" });
    const instance = hlsMock.instances[0]!;
    instance.handlers.get("mediaAttached")?.();
    instance.handlers.get("manifestParsed")?.();
    expect(instance.loadSource).toHaveBeenCalledWith(
      "/media-edge/sessions/SYN-SESSION-0001/master.m3u8",
    );
    instance.handlers.get("error")?.("error", { type: "mediaError", fatal: true });
    expect(instance.recoverMediaError).toHaveBeenCalledOnce();
    instance.handlers.get("error")?.("error", { type: "networkError", fatal: true });
    instance.handlers.get("error")?.("error", { type: "mediaError", fatal: false });
    expect(instance.recoverMediaError).toHaveBeenCalledOnce();
    adapter.teardown();
    expect(instance.stopLoad).toHaveBeenCalledOnce();
    expect(instance.destroy).toHaveBeenCalledOnce();
    expect(JSON.stringify(signals)).not.toContain("SYN-STREAM");
  });
  it("sends grants only to bounded media-edge resources", async () => {
    const adapter = createHlsAdapter(generatedPlaybackGrant(), {
      now,
      origin: "http://127.0.0.1:4173",
    });
    await adapter.attach(video());
    const instance = hlsMock.instances[0]!;
    const setRequestHeader = vi.fn();
    const abort = vi.fn();
    const xhr = { setRequestHeader, abort } as unknown as XMLHttpRequest;
    instance.config.xhrSetup(
      xhr,
      "http://127.0.0.1:4173/media-edge/sessions/SYN-SESSION-0001/segment-1.m4s",
    );
    expect(setRequestHeader).toHaveBeenCalledWith(
      "Authorization",
      expect.stringMatching(/^HCAM-Grant g1_/),
    );
    expect(() => instance.config.xhrSetup(xhr, "https://outside.invalid/segment-1.m4s")).toThrow(
      "media_resource_destination_rejected",
    );
    expect(abort).toHaveBeenCalledOnce();
  });
  it("denies expired grants before creating a decoder", async () => {
    const grant = { ...generatedPlaybackGrant(), expiresAt: "2026-09-08T09:00:00.000Z" };
    expect(await createHlsAdapter(grant, { now }).attach(video())).toEqual({
      state: "denied",
      reason: "grant_invalid",
    });
    expect(hlsMock.instances).toHaveLength(0);
    const adapter = createHlsAdapter(generatedPlaybackGrant(), { now });
    adapter.teardown();
  });
  it("reports unsupported MSE without creating a decoder", async () => {
    hlsMock.supported = false;
    expect(await createHlsAdapter(generatedPlaybackGrant(), { now }).attach(video())).toEqual({
      state: "unsupported",
      reason: "mse_unavailable",
    });
    expect(hlsMock.instances).toHaveLength(0);
  });
  it("supports injected module and instance factories", async () => {
    const instance = {
      handlers: new Map<string, (...args: unknown[]) => void>(),
      attachMedia: vi.fn(),
      loadSource: vi.fn(),
      once: vi.fn(),
      on: vi.fn(),
      stopLoad: vi.fn(),
      detachMedia: vi.fn(),
      destroy: vi.fn(),
      recoverMediaError: vi.fn(),
    };
    const module = await import("hls.js");
    const adapter = createHlsAdapter(generatedPlaybackGrant(), {
      now,
      loadModule: () => Promise.resolve(module),
      create: () => instance as never,
    });
    expect(await adapter.attach(video())).toEqual({ state: "attached", reason: "ready" });
    expect(instance.attachMedia).toHaveBeenCalledOnce();
    adapter.teardown();
  });
  it("uses the default clock for a currently valid generated grant", async () => {
    const timestamp = Date.now();
    const grant = {
      ...generatedPlaybackGrant(),
      issuedAt: new Date(timestamp - 1_000).toISOString(),
      expiresAt: new Date(timestamp + 60_000).toISOString(),
    };
    const adapter = createHlsAdapter(grant, { origin: "http://127.0.0.1:4173" });
    expect(await adapter.attach(video())).toEqual({ state: "attached", reason: "ready" });
    adapter.teardown();
  });
});
