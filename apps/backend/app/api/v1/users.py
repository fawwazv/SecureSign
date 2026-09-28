"""Profil user yang sedang login — GET /users/me + PATCH complete-profile."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from prisma import Prisma

from app.api.deps import get_current_user
from app.core.exceptions import AppError
from app.models.prisma_client import get_db
from app.schemas.auth import CompleteProfileRequest
from app.schemas.user import UserResponse, to_user_response
from app.services.audit_service import log_action

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


@router.patch(
    "/users/me/complete-profile", response_model=UserResponse, response_model_by_alias=True
)
async def complete_profile(
    payload: CompleteProfileRequest,
    request: Request,
    current: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Prisma, Depends(get_db)],
):
    user = await db.user.find_unique(where={"id": current["id"]})
    if user is None:
        raise AppError("UNAUTHORIZED", "Akun tidak ditemukan.", status=401)
    if user.profileCompleted:
        raise AppError("PROFILE_ALREADY_COMPLETED", "Profil sudah lengkap.", status=409)
    updated = await db.user.update(
        where={"id": user.id},
        data={
            "fullName": payload.full_name,
            "organization": payload.organization,
            "phone": payload.phone,
            "role": payload.role,
            "profileCompleted": True,
        },
    )
    await log_action(
        db,
        "PROFILE_COMPLETE",
        actor_id=user.id,
        entity="user",
        entity_id=user.id,
        details={"role": payload.role, "purpose": payload.purpose},
        ip_address=request.client.host if request.client else None,
    )
    return to_user_response(updated)
