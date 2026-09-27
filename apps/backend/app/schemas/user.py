"""Response user — camelCase persis kontrak openapi.yaml (User).

Catatan: prisma-client-py mengembalikan atribut dalam nama Prisma asli
(camelCase: fullName, emailVerified, ...), jadi helper ini membaca
atribut camelCase lalu memvalidasi via alias Pydantic.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    full_name: str = Field(alias="fullName")
    email: str
    organization: str
    role: str
    email_verified: bool = Field(alias="emailVerified")
    created_at: str = Field(alias="createdAt")


def to_user_response(user: object) -> dict:
    """User prisma -> dict camelCase siap JSON."""
    return UserResponse(
        id=user.id,  # type: ignore[attr-defined]
        fullName=user.fullName,  # type: ignore[attr-defined]
        email=user.email,  # type: ignore[attr-defined]
        organization=user.organization or "",  # type: ignore[attr-defined]
        role=str(user.role),  # type: ignore[attr-defined]
        emailVerified=user.emailVerified,  # type: ignore[attr-defined]
        createdAt=str(user.createdAt),  # type: ignore[attr-defined]
    ).model_dump(by_alias=True, mode="json")
