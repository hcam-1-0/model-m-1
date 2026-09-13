from __future__ import annotations

MAX_CONTRACT_BYTES = 64 * 1024
MAX_EVIDENCE_REFS = 256
MAX_REASON_BYTES = 2_000
MAX_PAGE_SIZE = 200
MAX_QUORUM = 5
MAX_TIMER_ATTEMPTS = 3
TIMER_LEASE_SECONDS = 90
MAX_BUDGET_LIMIT = 100_000
MAX_COLLAPSED_ALERTS = 10_000


def bounded_reason(value: str) -> str:
    encoded = value.encode("utf-8")
    if value.strip() != value or not 8 <= len(encoded) <= MAX_REASON_BYTES:
        raise ValueError("reason must be trimmed and 8 to 2000 UTF-8 bytes")
    return value


def bounded_page_size(value: int) -> int:
    if not 1 <= value <= MAX_PAGE_SIZE:
        raise ValueError("page size must be between 1 and 200")
    return value
