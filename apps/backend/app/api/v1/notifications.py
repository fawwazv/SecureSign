"""Endpoint notifikasi in-app milik user yang login."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from prisma import Prisma

from app.api.deps import get_current_user
from app.core.pagination import parse_pagination
from app.models.prisma_client import get_db
from app.schemas.document import to_notification_response

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=dict)
async def list_notifications(
    current: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Prisma, Depends(get_db)],
    page: int = 1,
    limit: int = 20,
):
    page, limit = parse_pagination(page, limit)
    where = {"userId": current["id"]}
    total = await db.notification.count(where=where)
    items = await db.notification.find_many(
        where=where, order={"createdAt": "desc"}, skip=(page - 1) * limit, take=limit
    )
    return {
        "data": [to_notification_response(n) for n in items],
        "page": page,
        "limit": limit,
        "total": total,
    }
