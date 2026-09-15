export interface MediaAttachResult {
  readonly state: "attached" | "unsupported" | "denied" | "fallback";
  readonly reason: string;
}
export interface MediaAdapter {
  readonly transport: "hls" | "native_hls" | "whep" | "none";
  readonly attach: (target: HTMLVideoElement) => Promise<MediaAttachResult>;
  readonly teardown: () => void;
}
export * from "./capabilities";
export * from "./hls-adapter";
export * from "./native-hls-adapter";
export * from "./no-media-adapter";
export * from "./telemetry";
export * from "./whep-adapter";
