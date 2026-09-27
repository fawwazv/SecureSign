"""Dependencies auth: get_current_user + require_role (RBAC 4 role, prd.md §4)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, Header

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import decode_token


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError("UNAUTHORIZED", "Token tidak ditemukan.", status=401)
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_token(token, settings.jwt_secret, expected_type="access")
    except ValueError as exc:
        raise AppError("UNAUTHORIZED", str(exc), status=401) from exc
    return {"id": payload["sub"], "role": payload.get("role")}


def require_role(*allowed: str):  # type: ignore[no-untyped-def]
    async def _checker(
        user: Annotated[dict[str, Any], Depends(get_current_user)],
    ) -> dict[str, Any]:
        if user.get("role") not in allowed:
            raise AppError("FORBIDDEN", "Role Anda tidak diizinkan.", status=403)
        return user

    return _checker
