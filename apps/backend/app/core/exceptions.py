"""Error terpusat — semua response error HARUS berbentuk {error: {code, message}} (prd.md §19)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details


def error_body(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}


def _validation_message(exc: RequestValidationError) -> str:
    parts: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
        parts.append(f"{loc}: {err.get('msg', 'tidak valid')}" if loc else str(err.get("msg")))
    return "; ".join(parts) or "Request tidak valid."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=error_body(exc.code, exc.message))

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 429: "RATE_LIMITED"}.get(
            exc.status_code, "HTTP_ERROR"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code, str(exc.detail) or "Terjadi kesalahan."),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422, content=error_body("VALIDATION_ERROR", _validation_message(exc))
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Jangan bocorkan detail internal ke klien; log ditangani middleware/logging.
        _ = exc
        return JSONResponse(
            status_code=500, content=error_body("INTERNAL_ERROR", "Terjadi kesalahan server.")
        )
