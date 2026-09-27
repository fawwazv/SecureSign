"""Endpoint auth — 6 endpoint persis openapi.yaml (tanpa forgot-password, ikut PRD ketat)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from prisma import Prisma

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_email_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.prisma_client import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    VerifyEmailRequest,
)
from app.schemas.user import UserResponse, to_user_response
from app.services.audit_service import log_action
from app.services.email_service import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])

VERIFY_EXPIRE_HOURS = 24


def _now() -> datetime:
    return datetime.now(UTC)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


async def _issue_token_pair(db: Prisma, user: Any) -> dict[str, Any]:
    access = create_access_token(
        user.id, str(user.role), settings.jwt_secret, settings.jwt_access_expire_minutes
    )
    refresh = create_refresh_token(
        user.id, settings.jwt_refresh_secret, settings.jwt_refresh_expire_days
    )
    await db.refreshtoken.create(
        data={
            "userId": user.id,
            "tokenHash": hash_refresh_token(refresh),
            "expiresAt": _now() + timedelta(days=settings.jwt_refresh_expire_days),
        }
    )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "expires_in": settings.jwt_access_expire_minutes * 60,
    }


@router.post(
    "/register", response_model=UserResponse, response_model_by_alias=True, status_code=201
)
async def register(
    payload: RegisterRequest, request: Request, db: Annotated[Prisma, Depends(get_db)]
):
    existing = await db.user.find_unique(where={"email": payload.email})
    if existing:
        raise AppError("EMAIL_TAKEN", "Email sudah terdaftar.", status=409)
    token = generate_email_token()
    user = await db.user.create(
        data={
            "email": payload.email,
            "passwordHash": hash_password(payload.password),
            "fullName": payload.full_name,
            "organization": payload.organization,
            "role": payload.role,
            "emailVerified": False,
            "verificationToken": token,
            "verificationExpiry": _now() + timedelta(hours=VERIFY_EXPIRE_HOURS),
        }
    )
    send_verification_email(user.email, token)
    await log_action(
        db,
        "REGISTER",
        actor_id=user.id,
        entity="user",
        entity_id=user.id,
        details={"purpose": payload.purpose, "role": payload.role},
        ip_address=_client_ip(request),
    )
    return to_user_response(user)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    payload: VerifyEmailRequest, request: Request, db: Annotated[Prisma, Depends(get_db)]
):
    user = await db.user.find_unique(where={"email": payload.email})
    if user is None:
        raise AppError("INVALID_TOKEN", "Token tidak valid atau sudah kedaluwarsa.", status=400)
    if user.emailVerified:
        return {"message": "Email sudah terverifikasi."}
    expired = user.verificationExpiry is None or user.verificationExpiry < _now()
    if user.verificationToken != payload.token or expired:
        raise AppError("INVALID_TOKEN", "Token tidak valid atau sudah kedaluwarsa.", status=400)
    await db.user.update(
        where={"id": user.id},
        data={"emailVerified": True, "verificationToken": None, "verificationExpiry": None},
    )
    await log_action(
        db,
        "VERIFY_EMAIL",
        actor_id=user.id,
        entity="user",
        entity_id=user.id,
        ip_address=_client_ip(request),
    )
    return {"message": "Email terverifikasi. Akun Anda sudah aktif."}


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    payload: ResendVerificationRequest, request: Request, db: Annotated[Prisma, Depends(get_db)]
):
    user = await db.user.find_unique(where={"email": payload.email})
    # Selalu 200 agar tidak membocorkan status akun (ikut openapi.yaml).
    if user is None or user.emailVerified:
        return {"message": "Jika email terdaftar, tautan verifikasi telah dikirim."}
    token = generate_email_token()
    await db.user.update(
        where={"id": user.id},
        data={
            "verificationToken": token,
            "verificationExpiry": _now() + timedelta(hours=VERIFY_EXPIRE_HOURS),
        },
    )
    send_verification_email(user.email, token)
    await log_action(
        db,
        "RESEND_VERIFICATION",
        actor_id=user.id,
        entity="user",
        entity_id=user.id,
        ip_address=_client_ip(request),
    )
    return {"message": "Jika email terdaftar, tautan verifikasi telah dikirim."}


@router.post("/login", response_model=LoginResponse, response_model_by_alias=True)
async def login(payload: LoginRequest, request: Request, db: Annotated[Prisma, Depends(get_db)]):
    user = await db.user.find_unique(where={"email": payload.email})
    if user is None or not verify_password(payload.password, user.passwordHash):
        raise AppError("INVALID_CREDENTIALS", "Email atau kata sandi salah.", status=401)
    if not user.emailVerified:
        raise AppError("EMAIL_NOT_VERIFIED", "Email belum terverifikasi.", status=403)
    tokens = await _issue_token_pair(db, user)
    await log_action(
        db,
        "LOGIN",
        actor_id=user.id,
        entity="user",
        entity_id=user.id,
        ip_address=_client_ip(request),
    )
    return {"user": to_user_response(user), "tokens": tokens}


@router.post("/refresh", response_model=LoginResponse, response_model_by_alias=True)
async def refresh(
    payload: RefreshRequest, request: Request, db: Annotated[Prisma, Depends(get_db)]
):
    try:
        claims = decode_token(payload.refresh_token, settings.jwt_refresh_secret, "refresh")
    except ValueError as exc:
        raise AppError("UNAUTHORIZED", str(exc), status=401) from exc
    row = await db.refreshtoken.find_unique(
        where={"tokenHash": hash_refresh_token(payload.refresh_token)}
    )
    if row is None or row.revoked or row.expiresAt < _now() or row.userId != claims["sub"]:
        raise AppError("UNAUTHORIZED", "Refresh token tidak valid.", status=401)
    # Rotation: revoke lama, terbitkan pasangan baru.
    await db.refreshtoken.update(where={"id": row.id}, data={"revoked": True})
    user = await db.user.find_unique(where={"id": row.userId})
    if user is None:
        raise AppError("UNAUTHORIZED", "Akun tidak ditemukan.", status=401)
    tokens = await _issue_token_pair(db, user)
    await log_action(
        db,
        "REFRESH",
        actor_id=user.id,
        entity="user",
        entity_id=user.id,
        ip_address=_client_ip(request),
    )
    return {"user": to_user_response(user), "tokens": tokens}


@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: LogoutRequest,
    request: Request,
    db: Annotated[Prisma, Depends(get_db)],
    _user: Annotated[dict, Depends(get_current_user)],
):
    row = await db.refreshtoken.find_unique(
        where={"tokenHash": hash_refresh_token(payload.refresh_token)}
    )
    if row is not None and not row.revoked:
        await db.refreshtoken.update(where={"id": row.id}, data={"revoked": True})
    await log_action(db, "LOGOUT", actor_id=_user["id"], ip_address=_client_ip(request))
    return {"message": "Logout sukses."}
