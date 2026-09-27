"""Audit log — immutable (hanya create + read, tanpa update/delete)."""

from __future__ import annotations

from typing import Any

from prisma import Json, Prisma


async def log_action(
    db: Prisma,
    action: str,
    actor_id: str | None = None,
    entity: str | None = None,
    entity_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> None:
    data: dict[str, Any] = {
        "action": action,
        "entity": entity,
        "entityId": entity_id,
        "details": Json(details or {}),
        "ipAddress": ip_address,
    }
    if actor_id is not None:
        data["actor"] = {"connect": {"id": actor_id}}
    await db.auditlog.create(data=data)
