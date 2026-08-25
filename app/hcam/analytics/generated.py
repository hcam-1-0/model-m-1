from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol

from hcam.analytics.runtime import RuntimeFailureCode, RuntimeInputDescriptorV1


GENERATED_FRAME_ID = "hcam.generated.det-r0-blocks.v1"
GENERATED_FRAME_VERSION = (
    "sha256:"
    + hashlib.sha256(
        b"hcam.generated.det-r0-blocks.v1:bgr8:416x416:top-left-blocks"
    ).hexdigest()
)
GENERATED_FRAME_WIDTH = 416
GENERATED_FRAME_HEIGHT = 416
MAX_ACTIVE_GENERATED_LEASES = 8


class GeneratedFrameLeaseError(RuntimeError):
    def __init__(self, code: RuntimeFailureCode) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class GeneratedFrame:
    width: int
    height: int
    data: bytes
    generator_id: str
    generator_version: str
    seed: int

    def __post_init__(self) -> None:
        if self.width != GENERATED_FRAME_WIDTH or self.height != GENERATED_FRAME_HEIGHT:
            raise ValueError("generated frame must use the approved 416x416 geometry")
        if len(self.data) != self.width * self.height * 3:
            raise ValueError("generated BGR frame byte count is invalid")
        if not 0 <= self.seed <= 4_294_967_295:
            raise ValueError("generated frame seed is outside the approved range")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest().upper()


@dataclass(frozen=True, slots=True)
class _Lease:
    descriptor: RuntimeInputDescriptorV1
    frame: GeneratedFrame


class RuntimeFrameResolver(Protocol):
    def consume(self, descriptor: RuntimeInputDescriptorV1) -> GeneratedFrame: ...


class GeneratedFrameLeaseStore:
    """Bounded consume-once memory storage; frame bytes never reach persistence."""

    def __init__(self, *, maximum_leases: int = MAX_ACTIVE_GENERATED_LEASES) -> None:
        if not 1 <= maximum_leases <= MAX_ACTIVE_GENERATED_LEASES:
            raise ValueError("generated lease capacity is outside the approved range")
        self._maximum_leases = maximum_leases
        self._leases: dict[str, _Lease] = {}
        self._lock = Lock()

    @property
    def active_leases(self) -> int:
        with self._lock:
            return len(self._leases)

    def issue(
        self,
        descriptor: RuntimeInputDescriptorV1,
        frame: GeneratedFrame,
    ) -> None:
        if descriptor.pixel_format != "bgr8":
            raise GeneratedFrameLeaseError("invalid_input")
        if (
            descriptor.source.width != frame.width
            or descriptor.source.height != frame.height
            or descriptor.source.timestamp_source != "generated"
        ):
            raise GeneratedFrameLeaseError("invalid_input")
        with self._lock:
            self._remove_expired_locked(datetime.now(UTC))
            if descriptor.lease_id in self._leases:
                raise GeneratedFrameLeaseError("invalid_input")
            if len(self._leases) >= self._maximum_leases:
                raise GeneratedFrameLeaseError("resource_exhausted")
            self._leases[descriptor.lease_id] = _Lease(descriptor, frame)

    def consume(self, descriptor: RuntimeInputDescriptorV1) -> GeneratedFrame:
        now = datetime.now(UTC)
        with self._lock:
            lease = self._leases.pop(descriptor.lease_id, None)
        if lease is None:
            raise GeneratedFrameLeaseError("input_expired")
        if lease.descriptor.input_id != descriptor.input_id:
            raise GeneratedFrameLeaseError("invalid_input")
        if now > descriptor.expires_at:
            raise GeneratedFrameLeaseError("input_expired")
        return lease.frame

    def revoke(self, lease_id: str) -> None:
        with self._lock:
            self._leases.pop(lease_id, None)

    def _remove_expired_locked(self, now: datetime) -> None:
        expired = [
            lease_id
            for lease_id, lease in self._leases.items()
            if now > lease.descriptor.expires_at
        ]
        for lease_id in expired:
            del self._leases[lease_id]


def _paint_block(
    pixels: bytearray,
    *,
    channel: int,
    x_start: int,
    x_end: int,
    y_start: int,
    y_end: int,
    value: int,
) -> None:
    for y in range(y_start, y_end):
        position = (y * GENERATED_FRAME_WIDTH + x_start) * 3 + channel
        for _ in range(x_start, x_end):
            pixels[position] = value
            position += 3


def generate_det_r0_frame(seed: int = 0) -> GeneratedFrame:
    if not 0 <= seed <= 4_294_967_295:
        raise ValueError("generated frame seed is outside the approved range")
    pixels = bytearray([114]) * (GENERATED_FRAME_WIDTH * GENERATED_FRAME_HEIGHT * 3)
    x_shift = 0 if seed == 0 else ((seed * 17 + 11) % 17) - 8
    y_shift = 0 if seed == 0 else ((seed * 29 + 7) % 17) - 8
    _paint_block(
        pixels,
        channel=0,
        x_start=156 + x_shift,
        x_end=260 + x_shift,
        y_start=104 + y_shift,
        y_end=312 + y_shift,
        value=220,
    )
    _paint_block(
        pixels,
        channel=1,
        x_start=80 - x_shift,
        x_end=336 - x_shift,
        y_start=150 - y_shift,
        y_end=260 - y_shift,
        value=64,
    )
    _paint_block(
        pixels,
        channel=2,
        x_start=104 + x_shift,
        x_end=312 + x_shift,
        y_start=208 - y_shift,
        y_end=312 - y_shift,
        value=180,
    )
    return GeneratedFrame(
        width=GENERATED_FRAME_WIDTH,
        height=GENERATED_FRAME_HEIGHT,
        data=bytes(pixels),
        generator_id=GENERATED_FRAME_ID,
        generator_version=GENERATED_FRAME_VERSION,
        seed=seed,
    )
