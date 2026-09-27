"""Request/response keys — camelCase persis kontrak openapi.yaml."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GenerateKeyRequest(BaseModel):
    algorithm: Literal["RSA_PSS_2048", "ECDSA_P256", "ED25519"]


class KeyPairResponse(BaseModel):
    id: str
    algorithm: str
    public_key: str = Field(alias="publicKey")
    revoked: bool
    revoked_at: datetime | None = Field(default=None, alias="revokedAt")
    created_at: datetime = Field(alias="createdAt")


def to_key_response(key: object) -> dict:
    return KeyPairResponse(
        id=key.id,  # type: ignore[attr-defined]
        algorithm=str(key.algorithm),  # type: ignore[attr-defined]
        publicKey=key.publicKey,  # type: ignore[attr-defined]
        revoked=key.revoked,  # type: ignore[attr-defined]
        revokedAt=key.revokedAt,  # type: ignore[attr-defined]
        createdAt=str(key.createdAt),  # type: ignore[attr-defined]
    ).model_dump(by_alias=True, mode="json")
