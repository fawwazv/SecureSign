"""Rate limiting: default 60 req/menit per IP (prd.md §19), auth sensitif 10/menit.

In-memory sliding window. Untuk produksi multi-worker gunakan Redis.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import error_body

_hits: dict[str, deque[float]] = defaultdict(deque)

# Path auth sensitif -> limit khusus (dokumen otorisasi §8). Cocokkan prefix.
DEFAULT_PATH_LIMITS: dict[str, int] = {}


def rate_limit_middleware(
    limit_per_minute: int, path_limits: dict[str, int] | None = None
):  # type: ignore[no-untyped-def]
    limits = dict(DEFAULT_PATH_LIMITS)
    if path_limits:
        limits.update(path_limits)

    async def _middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)
        limit = limit_per_minute
        scope = "default"
        for prefix, custom in limits.items():
            if request.url.path.startswith(prefix):
                limit = custom
                scope = prefix
                break
        ip = request.client.host if request.client else "unknown"
        key = f"{ip}|{scope}"
        now = time.monotonic()
        window = _hits[key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= limit:
            return JSONResponse(
                status_code=429,
                content=error_body("RATE_LIMITED", "Terlalu banyak request. Coba lagi sebentar."),
            )
        window.append(now)
        return await call_next(request)

    return _middleware


def reset_rate_limiter() -> None:
    """Dipakai test agar antar-test tidak saling mengotori."""
    _hits.clear()
