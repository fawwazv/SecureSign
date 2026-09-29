"""Endpoint sign-requests — pending (Fase 3), approve/batch/reject (Fase 4)."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from prisma import Prisma

from app.api.deps import require_role
from app.core.exceptions import AppError
from app.core.pagination import parse_pagination
from app.models.prisma_client import get_db
from app.schemas.document import to_sign_request_response
from app.schemas.signature import SignatureResponse, to_signature_response
from app.services.audit_service import log_action
from app.services.notification_service import notify
from app.services.signing_service import approve_one

router = APIRouter(tags=["sign-requests"])

SignerOnly = Annotated[dict[str, Any], Depends(require_role("SIGNER", "SUPER_ADMIN"))]


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


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


@router.post(
    "/sign-requests/{id}/approve",
    status_code=201,
    response_model=SignatureResponse,
    response_model_by_alias=True,
)
async def approve(
    id: str,
    payload: dict[str, Any],
    user: SignerOnly,
    request: Request,
    db: Annotated[Prisma, Depends(get_db)],
):
    key_pair_id = payload.get("keyPairId", "")
    if not key_pair_id:
        raise AppError("MISSING_KEY", "keyPairId wajib diisi.", status=400)
    position = payload.get("position")
    if position is not None and (not isinstance(position, str) or len(position.strip()) == 0):
        raise AppError("INVALID_POSITION", "position harus teks tidak kosong.", status=400)
    async with db.tx(timeout=30000) as tx:
        sig = await approve_one(tx, id, user["id"], key_pair_id, _ip(request), position)
    return to_signature_response(sig)


@router.post("/sign-requests/batch-approve", response_model=dict)
async def batch_approve(
    payload: dict[str, Any],
    user: SignerOnly,
    request: Request,
    db: Annotated[Prisma, Depends(get_db)],
):
    items = payload.get("items", [])
    if not items:
        raise AppError("EMPTY_BATCH", "items tidak boleh kosong.", status=400)
    results: list[dict[str, Any]] = []
    for item in items:
        sr_id = item.get("signRequestId", "")
        key_id = item.get("keyPairId", "")
        position = item.get("position")
        try:
            async with db.tx(timeout=30000) as tx:
                sig = await approve_one(tx, sr_id, user["id"], key_id, _ip(request), position)
            results.append(
                {"signRequestId": sr_id, "success": True, "signatureId": sig.id, "error": None}
            )
        except AppError as exc:
            results.append(
                {
                    "signRequestId": sr_id,
                    "success": False,
                    "signatureId": None,
                    "error": {"error": {"code": exc.code, "message": exc.message}},
                }
            )
    return {"results": results}


@router.post("/sign-requests/{id}/reject", response_model=dict)
async def reject(
    id: str,
    payload: dict[str, Any],
    user: SignerOnly,
    request: Request,
    db: Annotated[Prisma, Depends(get_db)],
):
    reason = (payload.get("rejectReason") or "").strip()
    if not reason:
        raise AppError("MISSING_REASON", "rejectReason wajib diisi.", status=400)
    sr = await db.signrequest.find_unique(where={"id": id})
    if sr is None or sr.signerId != user["id"]:
        raise AppError("NOT_FOUND", "Sign request tidak ditemukan.", status=404)
    if sr.status != "PENDING":
        raise AppError("ALREADY_DECIDED", "Request sudah diputuskan.", status=409)
    updated = await db.signrequest.update(
        where={"id": id}, data={"status": "REJECTED", "rejectReason": reason}
    )
    doc = await db.document.find_unique(where={"id": sr.documentId})
    if doc:
        await db.document.update(where={"id": doc.id}, data={"status": "REJECTED"})
        await notify(
            db, doc.uploaderId, "REJECTED", "Dokumen ditolak", f"'{doc.title}' ditolak: {reason}"
        )
    await log_action(
        db,
        "REJECT",
        actor_id=user["id"],
        entity="sign_request",
        entity_id=id,
        details={"reason": reason},
        ip_address=_ip(request),
    )
    return to_sign_request_response(updated)
