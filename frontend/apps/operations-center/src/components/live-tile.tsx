import { CircleX, Pause, Play, VolumeX } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { AdmissionDecision, StreamProjection } from "@hcam/camera-live-domain";
import {
  createHlsAdapter,
  createNativeHlsAdapter,
  createNoMediaAdapter,
  createWhepAdapter,
  type MediaAdapter,
} from "@hcam/media-adapters";
import type { PlaybackSessionGrant } from "@hcam/media-edge-contracts";
import { generatedNow } from "../data/camera-live-projections";
import { PlayerStatus, type PlayerState } from "./player-status";

function adapterFor(decision: AdmissionDecision, grant: PlaybackSessionGrant): MediaAdapter {
  const options = { now: () => generatedNow };
  if (!decision.admitted) return createNoMediaAdapter(decision.reason);
  if (decision.transport === "hls") return createHlsAdapter(grant, options);
  if (decision.transport === "native_hls") return createNativeHlsAdapter(grant, options);
  if (decision.transport === "whep")
    return createWhepAdapter(grant, { ...options, enabled: false });
  return createNoMediaAdapter();
}

export function LiveTile({
  stream,
  decision,
  grant,
  compact = false,
}: {
  readonly stream: StreamProjection;
  readonly decision: AdmissionDecision;
  readonly grant: PlaybackSessionGrant;
  readonly compact?: boolean;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const adapterRef = useRef<MediaAdapter | null>(null);
  const [paused, setPaused] = useState(false);
  const [status, setStatus] = useState<{ state: PlayerState; reason: string }>({
    state: "idle",
    reason: "generated_only",
  });
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return undefined;
    if (!decision.admitted) return undefined;
    const adapter = adapterFor(decision, grant);
    adapterRef.current = adapter;
    let active = true;
    void Promise.resolve()
      .then(async () => {
        if (active) setStatus({ state: "loading", reason: "generated_only" });
        return await adapter.attach(video);
      })
      .then((result) => {
        if (!active) return;
        setStatus({ state: result.state, reason: result.reason });
        if (result.state === "attached") void video.play().catch(() => undefined);
      })
      .catch(() => {
        if (active) setStatus({ state: "unavailable", reason: "manifest_invalid" });
      });
    const releaseForBoundary = (reason: string) => {
      if (!active) return;
      active = false;
      adapter.teardown();
      adapterRef.current = null;
      setPaused(false);
      setStatus({ state: "released", reason });
    };
    const onVisibilityChange = () => {
      if (document.hidden) releaseForBoundary("document_hidden");
    };
    const onPageHide = () => releaseForBoundary("page_hidden");
    document.addEventListener("visibilitychange", onVisibilityChange);
    window.addEventListener("pagehide", onPageHide);
    return () => {
      active = false;
      document.removeEventListener("visibilitychange", onVisibilityChange);
      window.removeEventListener("pagehide", onPageHide);
      adapter.teardown();
      adapterRef.current = null;
    };
  }, [decision, grant]);
  const togglePause = () => {
    const video = videoRef.current;
    if (!video || !adapterRef.current) return;
    if (paused) {
      void video
        .play()
        .then(() => {
          setPaused(false);
          setStatus({ state: "attached", reason: "ready" });
        })
        .catch(() => setStatus({ state: "unavailable", reason: "playback_rejected" }));
      return;
    }
    video.pause();
    setPaused(true);
    setStatus({ state: "paused", reason: "operator_pause" });
  };
  const release = () => {
    adapterRef.current?.teardown();
    adapterRef.current = null;
    setPaused(false);
    setStatus({ state: "released", reason: "operator_release" });
  };
  const controllable = status.state === "attached" || status.state === "paused";
  const visibleStatus = decision.admitted
    ? status
    : ({ state: "held", reason: decision.reason } satisfies typeof status);
  return (
    <article className={compact ? "live-tile compact" : "live-tile"} data-stream-id={stream.id}>
      <div className="video-frame">
        <video
          ref={videoRef}
          muted
          autoPlay
          playsInline
          aria-label={`Generated live view for ${stream.label}`}
        />
        <div className="video-grid" aria-hidden="true" />
        <span className="generated-watermark">GENERATED</span>
        <PlayerStatus state={visibleStatus.state} reason={visibleStatus.reason} />
      </div>
      <footer>
        <div>
          <strong>{stream.label}</strong>
          <small>{stream.id}</small>
        </div>
        <span>
          {decision.transport.toUpperCase()} · {decision.rendition ?? "held"}
        </span>
        <button
          type="button"
          title="Audio disabled"
          aria-label={`Audio disabled for ${stream.label}`}
          disabled
        >
          <VolumeX size={15} />
        </button>
        <button
          type="button"
          title={paused ? "Resume generated view" : "Pause generated view"}
          aria-label={`${paused ? "Resume" : "Pause"} ${stream.label}`}
          disabled={!controllable}
          onClick={togglePause}
        >
          {paused ? <Play size={15} /> : <Pause size={15} />}
        </button>
        <button
          type="button"
          title="Release generated view"
          aria-label={`Release ${stream.label}`}
          disabled={!controllable}
          onClick={release}
        >
          <CircleX size={15} />
        </button>
      </footer>
    </article>
  );
}
