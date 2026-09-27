"""Profil user yang sedang login — GET /users/me (ikut prd-backend ketat)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from prisma import Prisma

from app.api.deps import get_current_user
from app.core.exceptions import AppError
from app.models.prisma_client import get_db
from app.schemas.user import UserResponse, to_user_response

router = APIRouter(tags=["users"])


@router.get("/users/me", response_model=UserResponse, response_model_by_alias=True)
async def get_me(
    current: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Prisma, Depends(get_db)],
):
    user = await db.user.find_unique(where={"id": current["id"]})
    if user is None:
        raise AppError("UNAUTHORIZED", "Akun tidak ditemukan.", status=401)
    return to_user_response(user)
