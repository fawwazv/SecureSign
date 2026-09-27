"""Rate limiting sederhana: 60 req/menit per IP (prd.md §19), in-memory sliding window."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import error_body

_hits: dict[str, deque[float]] = defaultdict(deque)


def rate_limit_middleware(limit_per_minute: int):  # type: ignore[no-untyped-def]
    async def _middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = _hits[ip]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= limit_per_minute:
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
