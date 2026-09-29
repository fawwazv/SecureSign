"""Request/response auth — camelCase persis kontrak openapi.yaml."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.user import UserResponse

ALLOWED_REGISTER_ROLES = ("ORG_ADMIN", "SIGNER")
PHONE_RE = re.compile(r"^[+0-9][0-9\s\-()]{6,19}$")


def _normalize_phone(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"[\s\-()]", "", value)
    if not PHONE_RE.match(value) or len(normalized) < 7:
        raise ValueError("Nomor telepon tidak valid.")
    return normalized


class RegisterRequest(BaseModel):
    full_name: str = Field(alias="fullName", min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    organization: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    role: Literal["ORG_ADMIN", "SIGNER"]
    purpose: str = Field(min_length=3, max_length=500)
    captcha_token: str | None = Field(alias="captchaToken", default=None)

    @field_validator("phone")
    @classmethod
    def _normalize_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = re.sub(r"[\s\-()]", "", value)
        if not PHONE_RE.match(value) or len(normalized) < 7:
            raise ValueError("Nomor telepon tidak valid.")
        return normalized


class GoogleLoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_token: str = Field(alias="idToken", min_length=1)


class CompleteProfileRequest(BaseModel):
    full_name: str = Field(alias="fullName", min_length=3, max_length=100)
    organization: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=7, max_length=20)
    role: Literal["ORG_ADMIN", "SIGNER"]
    purpose: str = Field(min_length=3, max_length=500)

    @field_validator("phone")
    @classmethod
    def _normalize_phone(cls, value: str) -> str:
        normalized = re.sub(r"[\s\-()]", "", value)
        if not PHONE_RE.match(value) or len(normalized) < 7:
            raise ValueError("Nomor telepon tidak valid.")
        return normalized


class GoogleLoginResponse(BaseModel):
    user: UserResponse
    tokens: AuthTokensResponse
    profile_completed: bool = Field(alias="profileCompleted")


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    token: str = Field(min_length=1)


class ResendVerificationRequest(BaseModel):
    email: EmailStr
    captcha_token: str | None = Field(alias="captchaToken", default=None)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    captcha_token: str | None = Field(alias="captchaToken", default=None)


class RefreshRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    refresh_token: str = Field(alias="refreshToken", min_length=1)


class LogoutRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    refresh_token: str = Field(alias="refreshToken", min_length=1)


class AuthTokensResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    expires_in: int = Field(alias="expiresIn")


class MessageResponse(BaseModel):
    message: str


class LoginResponse(BaseModel):
    user: UserResponse
    tokens: AuthTokensResponse
