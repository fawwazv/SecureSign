"""Request/response auth — camelCase persis kontrak openapi.yaml."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.user import UserResponse

ALLOWED_REGISTER_ROLES = ("ORG_ADMIN", "SIGNER")


class RegisterRequest(BaseModel):
    full_name: str = Field(alias="fullName", min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    organization: str = Field(min_length=1, max_length=100)
    role: Literal["ORG_ADMIN", "SIGNER"]
    purpose: str = Field(min_length=1, max_length=500)


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    token: str = Field(min_length=1)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


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
