"""Endpoint sign-requests — Fase 3: daftar pending (Signer).
Approve / batch-approve / reject menyusul Fase 4.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from prisma import Prisma

from app.api.deps import require_role
from app.core.pagination import parse_pagination
from app.models.prisma_client import get_db
from app.schemas.document import to_sign_request_response

router = APIRouter(tags=["sign-requests"])

SignerOnly = Annotated[dict[str, Any], Depends(require_role("SIGNER"))]


@router.get("/sign-requests/pending", response_model=dict)
async def list_pending(
    user: SignerOnly,
    db: Annotated[Prisma, Depends(get_db)],
    page: int = 1,
    limit: int = 20,
):
    page, limit = parse_pagination(page, limit)
    where = {"signerId": user["id"], "status": "PENDING"}
    total = await db.signrequest.count(where=where)
    items = await db.signrequest.find_many(
        where=where, order={"createdAt": "desc"}, skip=(page - 1) * limit, take=limit
    )
    return {
        "data": [to_sign_request_response(s) for s in items],
        "page": page,
        "limit": limit,
        "total": total,
    }
