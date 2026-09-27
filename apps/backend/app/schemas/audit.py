"""Response audit log — camelCase persis openapi.yaml."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    id: str
    actor_id: str | None = Field(default=None, alias="actorId")
    action: str
    entity: str | None = None
    entity_id: str | None = Field(default=None, alias="entityId")
    details: dict[str, Any] = {}
    ip_address: str | None = Field(default=None, alias="ipAddress")
    created_at: str = Field(alias="createdAt")


def to_audit_response(a: object) -> dict:
    details = a.details  # type: ignore[attr-defined]
    return AuditLogResponse(
        id=a.id,  # type: ignore[attr-defined]
        actorId=a.actorId,  # type: ignore[attr-defined]
        action=a.action,  # type: ignore[attr-defined]
        entity=a.entity,  # type: ignore[attr-defined]
        entityId=a.entityId,  # type: ignore[attr-defined]
        details=dict(details) if isinstance(details, dict) else {},
        ipAddress=a.ipAddress,  # type: ignore[attr-defined]
        createdAt=str(a.createdAt),  # type: ignore[attr-defined]
    ).model_dump(by_alias=True, mode="json")
