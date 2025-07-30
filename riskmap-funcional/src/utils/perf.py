"""Simple performance middleware to measure endpoint latency and count.
Stores statistics in-memory and exposes helper to retrieve them.
"""

import time
import asyncio
from collections import defaultdict
from copy import deepcopy
from typing import Dict, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


__all__ = [
    "PerfMiddleware",
    "get_stats",
    "reset_stats",
]

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

# A simple in-memory dictionary that stores latency information per path.
# Each key is the request path and its value is another mapping with the
# following structure::
#
#     {
#         "count": <number of requests>,
#         "sum": <cumulative latency>,
#         "avg": <average latency>,
#         "min": <fastest request>,
#         "max": <slowest request>,
#     }
#
# The defaultdict takes care of the initialisation so the rest of the code can
# be blissfully unaware of missing keys.
_stats: Dict[str, Dict[str, float]] = defaultdict(
    lambda: {"count": 0, "sum": 0.0, "avg": 0.0, "min": float("inf"), "max": 0.0}
)

# Guard concurrent updates – FastAPI / Starlette might serve requests in
# multiple asyncio tasks at the same time so we need a lock to avoid lost
# updates.
_stats_lock: asyncio.Lock = asyncio.Lock()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class PerfMiddleware(BaseHTTPMiddleware):
    """Middleware that records basic latency statistics per endpoint path."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        finally:
            duration = time.perf_counter() - start
            path = request.url.path
            # update the shared stats dictionary in a critical section
            async with _stats_lock:
                stats = _stats[path]
                stats["count"] += 1
                stats["sum"] += duration
                stats["avg"] = stats["sum"] / stats["count"]
                stats["min"] = min(stats["min"], duration)
                stats["max"] = max(stats["max"], duration)
        return response


def get_stats(copy: bool = True) -> Dict[str, Dict[str, Any]]:
    """Return the currently collected statistics.

    Parameters
    ----------
    copy:
        When *True* (default) a deep copy of the internal structure is
        returned so external code cannot mutate the internal cache. Disable if
        you know what you're doing and want to avoid the small copy expense.
    """
    # We don't need the lock for reading shallow copies but it's safer to use
    # it so the snapshot is fully consistent.
    async def _snapshot():
        async with _stats_lock:
            return deepcopy(_stats) if copy else dict(_stats)

    # Because *get_stats* is regular sync function we need to run the coroutine
    # to obtain the data – we rely on the fact that FastAPI always runs inside
    # an event-loop, otherwise this would block.
    return asyncio.get_event_loop().run_until_complete(_snapshot())


async def reset_stats() -> None:
    """Clear all collected statistics."""
    async with _stats_lock:
        _stats.clear()
