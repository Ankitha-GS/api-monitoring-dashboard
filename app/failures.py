"""Failure registry: structured logs + in-memory ring buffer used for root cause analysis."""
import json
import logging
from collections import deque
from datetime import datetime, timezone

from .metrics import FAILURES

logger = logging.getLogger("api.failures")
RECENT: deque = deque(maxlen=200)

ROOT_CAUSE_HINTS = {
    "authentication": "Client sent a missing or invalid X-API-Key. Check key rotation, client config or an attacker probing the API.",
    "rate_limit": "Client exceeded the allowed request quota. Check for retry loops / abusive clients; honour the Retry-After header.",
    "server_error": "Unhandled exception inside the application. See 'exception_type', 'message' and 'traceback' for the failing code path.",
    "slow_response": "Request exceeded the slow-response threshold. Check downstream dependencies, DB queries, CPU/memory saturation.",
    "health_check": "Health check reported an unhealthy dependency (database or forced failure). Check the 'checks' details.",
}


def record_failure(category: str, **details) -> dict:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "category": category,
        "root_cause_hint": ROOT_CAUSE_HINTS.get(category, "n/a"),
        **details,
    }
    RECENT.appendleft(entry)
    FAILURES.labels(category).inc()
    logger.error(json.dumps(entry, default=str))
    return entry
