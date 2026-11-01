"""Sliding-window in-memory rate limiter (per client)."""
import time
from collections import defaultdict, deque

from . import config

_hits: dict[str, deque] = defaultdict(deque)


def hit(client: str) -> tuple[bool, int, int]:
    """Register a request. Returns (allowed, remaining, retry_after_seconds)."""
    now = time.monotonic()
    window = _hits[client]
    while window and now - window[0] > config.RATE_LIMIT_WINDOW:
        window.popleft()
    if len(window) >= config.RATE_LIMIT_MAX:
        retry_after = max(1, int(config.RATE_LIMIT_WINDOW - (now - window[0])) + 1)
        return False, 0, retry_after
    window.append(now)
    return True, config.RATE_LIMIT_MAX - len(window), 0


def reset() -> None:
    _hits.clear()
