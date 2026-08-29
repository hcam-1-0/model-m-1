from __future__ import annotations

import gc
import random
import threading
import time
from pathlib import Path
from typing import Callable

from .config import AdapterConfig, StreamConfig
from .recorder import build_ffmpeg_segment_cmd, ensure_camera_dirs, popen_recorder, terminate_recorder
from .analytics import FrameSampler
from .telemetry import TelemetryLoop


def exponential_backoff(attempt: int, base: float, cap: float, jitter: float) -> float:
    """Compute backoff with full jitter."""
    exp = min(cap, base * (2 ** attempt))
    if jitter <= 0:
        return exp
    # Randomize between exp*(1-jitter) and exp
    low = exp * (1 - jitter)
    return random.uniform(low, exp)


class CameraWorker(threading.Thread):
    """Isolated per-camera thread: FFmpeg recorder + sampled YOLO analytics."""

    def __init__(
        self,
        stream: StreamConfig,
        cfg: AdapterConfig,
        base: Path,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(name=f"hcam-worker-{stream.camera_id}", daemon=True)
        self.stream = stream
        self.cfg = cfg
        self.base = base
        self.logger = logger or (lambda msg: print(msg, flush=True))
        self._stop_event = threading.Event()
        self._proc = None
        self._sampler: FrameSampler | None = None

    def _log(self, msg: str) -> None:
        try:
            self.logger(f"[{self.stream.camera_id}] {msg}")
        except Exception:
            pass

    def stop(self) -> None:
        self._stop_event.set()
        if self._proc is not None:
            try:
                terminate_recorder(self._proc)
            except Exception:
                pass
        if self._sampler is not None:
            try:
                self._sampler.close()
            except Exception:
                pass

    def run(self) -> None:
        attempt = 0
        # Ensure dirs once
        _, segments_dir, detections_dir = ensure_camera_dirs(self.base, self.stream.camera_id)
        log_path = self.base / self.stream.camera_id / "ffmpeg.log"

        # Lazy sampler init
        try:
            self._sampler = FrameSampler(
                rtsp_url=self.stream.rtsp_url,
                camera_id=self.stream.camera_id,
                detections_dir=detections_dir,
                sample_interval=self.cfg.sample_interval_seconds,
                yolo_model=self.cfg.yolo_model,
                yolo_conf=self.cfg.yolo_conf,
                yolo_classes=self.cfg.yolo_classes,
                yolo_device=self.cfg.yolo_device,
                rtsp_transport=self.cfg.rtsp_transport,
            )
        except Exception as e:
            self._log(f"sampler init failed (analytics disabled): {e}")
            self._sampler = None

        # Output pattern for segment muxer
        # Uses strftime: cam_01_2026-08-26_14-30-00.mp4
        # The segment muxer will create a new file every segment_time
        pattern = str(segments_dir / f"{self.stream.camera_id}_%Y-%m-%d_%H-%M-%S.mp4")

        cmd = build_ffmpeg_segment_cmd(
            ffmpeg_bin=self.cfg.ffmpeg_bin,
            rtsp_url=self.stream.rtsp_url,
            output_pattern=pattern,
            segment_time=self.cfg.segment_time_seconds,
            rtsp_transport=self.cfg.rtsp_transport,
            extra_input_args=self.cfg.extra_ffmpeg_input_args,
            extra_output_args=self.cfg.extra_ffmpeg_output_args,
        )
        # Do not log the complete command: an authorized source URL can contain
        # credentials and this log is persisted beside camera recordings.
        self._log("FFmpeg recorder prepared")

        while not self._stop_event.is_set():
            # Check max attempts (0 = infinite)
            if self.cfg.max_reconnect_attempts and attempt >= self.cfg.max_reconnect_attempts:
                self._log(f"max reconnect attempts ({self.cfg.max_reconnect_attempts}) reached — stopping")
                break

            if attempt > 0:
                backoff = exponential_backoff(attempt - 1, self.cfg.backoff_base_seconds, self.cfg.backoff_max_seconds, self.cfg.backoff_jitter)
                self._log(f"reconnect attempt {attempt} backoff {backoff:.1f}s")
                if self._stop_event.wait(backoff):
                    break

            self._log(f"starting recorder (attempt {attempt}) -> {pattern}")
            try:
                self._proc = popen_recorder(cmd, log_path)
            except Exception as e:
                self._log(f"popen failed: {e}")
                attempt += 1
                continue

            # Inner loop: monitor FFmpeg + run analytics sampling
            # We poll proc every ~0.5s and interleave analytics
            healthy_since = time.monotonic()
            while not self._stop_event.is_set():
                # Check if FFmpeg died
                ret = self._proc.poll()
                if ret is not None:
                    self._log(f"FFmpeg exited code={ret} — will reconnect (see {log_path})")
                    # Cleanup log handle
                    try:
                        lf = getattr(self._proc, "_log_file", None)
                        if lf:
                            lf.close()
                    except Exception:
                        pass
                    self._proc = None
                    # Force sampler reconnect too
                    if self._sampler is not None:
                        try:
                            self._sampler.close()
                        except Exception:
                            pass
                    break

                # Analytics sampling (zero-copy, gc)
                if self._sampler is not None:
                    try:
                        payload = self._sampler.sample_once()
                        if payload is not None and payload.get("count", 0) >= 0:
                            # Always write file even if 0 detections? Write only if detections present
                            # to reduce Drive IOPS — but also write empty with flag for audit
                            # We write all samples to keep timeline; comment out if noisy
                            out = self._sampler.write_detection(payload)
                            if payload["count"] > 0:
                                self._log(f"YOLO detections={payload['count']} -> {out.name}")
                    except Exception as e:
                        self._log(f"analytics sample error: {e}")
                    # Explicit gc hint after each sample window
                    gc.collect()

                # If healthy for 90s, reset backoff
                if time.monotonic() - healthy_since > 90 and attempt != 0:
                    self._log("healthy for 90s — resetting backoff")
                    attempt = 0
                    healthy_since = time.monotonic()

                # Sleep briefly, responsive to stop
                if self._stop_event.wait(0.5):
                    break

            # If inner loop exited due to stop, cleanup and exit outer
            if self._stop_event.is_set():
                if self._proc is not None:
                    try:
                        terminate_recorder(self._proc)
                    except Exception:
                        pass
                    self._proc = None
                break

            # Otherwise FFmpeg died — increment attempt and reconnect
            attempt += 1

        self._log("worker stopped")
        if self._sampler is not None:
            try:
                self._sampler.close()
            except Exception:
                pass


class AdapterOrchestrator:
    """Manages N CameraWorkers + telemetry thread."""

    def __init__(self, cfg: AdapterConfig, base: Path | None = None, logger: Callable[[str], None] | None = None) -> None:
        self.cfg = cfg
        self.base = base or cfg.effective_base()
        self.logger = logger or (lambda msg: print(msg, flush=True))
        self.workers: list[CameraWorker] = []
        self.telemetry = TelemetryLoop(
            base=self.base,
            interval=self.cfg.telemetry_interval_seconds,
            logger=self.logger,
            log_file=self.base / "_telemetry.log",
        )

    def start(self) -> None:
        if self.workers:
            self.logger("[orchestrator] already started")
            return
        self.base.mkdir(parents=True, exist_ok=True)
        self.telemetry.start()
        for s in self.cfg.streams:
            if not s.enabled:
                continue
            w = CameraWorker(stream=s, cfg=self.cfg, base=self.base, logger=self.logger)
            w.start()
            self.workers.append(w)
        self.logger(f"[orchestrator] started {len(self.workers)} workers @ base={self.base}")

    def stop(self) -> None:
        self.logger("[orchestrator] stopping...")
        self.telemetry.stop()
        for w in self.workers:
            w.stop()
        for w in self.workers:
            w.join(timeout=10)
        self.workers.clear()
        self.logger("[orchestrator] all workers stopped")

    def wait(self) -> None:
        """Block until all workers exit (or KeyboardInterrupt)."""
        try:
            while any(w.is_alive() for w in self.workers):
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
