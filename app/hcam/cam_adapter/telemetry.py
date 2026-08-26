from __future__ import annotations

import os
import shutil
import threading
import time
from pathlib import Path
from typing import Callable

try:
    import psutil  # type: ignore
except ImportError:
    psutil = None  # type: ignore

try:
    import torch  # type: ignore
except ImportError:
    torch = None  # type: ignore


def _human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024  # type: ignore
    return f"{n:.1f}PB"


def collect_drive_usage(base: Path) -> tuple[int, int]:
    """Return (total_bytes, file_count) under base (segments only)."""
    total = 0
    count = 0
    if not base.exists():
        return 0, 0
    for p in base.rglob("*.mp4"):
        try:
            total += p.stat().st_size
            count += 1
        except Exception:
            continue
    # Also count detections
    det_count = 0
    for p in base.rglob("*.json"):
        det_count += 1
    return total, count


def collect_system_stats() -> dict:
    stats: dict = {}
    if psutil is not None:
        try:
            stats["cpu_percent"] = psutil.cpu_percent(interval=None)
            vm = psutil.virtual_memory()
            stats["ram_percent"] = vm.percent
            stats["ram_used"] = _human_bytes(vm.used)
            stats["ram_total"] = _human_bytes(vm.total)
            du = psutil.disk_usage(str(Path.cwd()))
            stats["disk_percent"] = du.percent
        except Exception as e:
            stats["psutil_error"] = str(e)
    else:
        stats["psutil"] = "not_installed"

    if torch is not None and torch.cuda.is_available():
        try:
            stats["cuda_available"] = True
            stats["cuda_device_count"] = torch.cuda.device_count()
            for i in range(torch.cuda.device_count()):
                stats[f"gpu_{i}_mem_allocated"] = _human_bytes(torch.cuda.memory_allocated(i))
                stats[f"gpu_{i}_mem_reserved"] = _human_bytes(torch.cuda.memory_reserved(i))
        except Exception as e:
            stats["cuda_error"] = str(e)
    else:
        stats["cuda_available"] = False
    return stats


class TelemetryLoop:
    """Non-blocking daemon thread that logs Drive usage + CPU/GPU/RAM every N seconds."""

    def __init__(
        self,
        base: Path,
        interval: float = 30.0,
        logger: Callable[[str], None] | None = None,
        log_file: Path | None = None,
    ) -> None:
        self.base = base
        self.interval = interval
        self.logger = logger or (lambda msg: print(msg, flush=True))
        self.log_file = log_file
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="hcam-telemetry", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _log(self, msg: str) -> None:
        try:
            self.logger(msg)
        except Exception:
            pass
        if self.log_file is not None:
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass

    def _loop(self) -> None:
        # Prime psutil cpu_percent
        if psutil is not None:
            try:
                psutil.cpu_percent(interval=None)
            except Exception:
                pass
        while not self._stop.is_set():
            try:
                total_bytes, seg_count = collect_drive_usage(self.base)
                sys_stats = collect_system_stats()
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                line = (
                    f"[{ts}] TELEMETRY base={self.base} segments={seg_count} "
                    f"drive_used={_human_bytes(total_bytes)} "
                    f"cpu={sys_stats.get('cpu_percent', '?')}% "
                    f"ram={sys_stats.get('ram_percent', '?')}%({sys_stats.get('ram_used','?')}/{sys_stats.get('ram_total','?')}) "
                    f"disk={sys_stats.get('disk_percent','?')}% "
                    f"cuda={sys_stats.get('cuda_available', False)}"
                )
                # Add GPU details if present
                for k, v in sys_stats.items():
                    if k.startswith("gpu_"):
                        line += f" {k}={v}"
                self._log(line)
            except Exception as e:
                self._log(f"[telemetry] error: {e}")
            # Wait with early exit on stop
            self._stop.wait(self.interval)
