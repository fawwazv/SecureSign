"""Endpoint documents — upload/list/detail (Org Admin) + request-sign."""

from __future__ import annotations

import json
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, UploadFile
from prisma import Json, Prisma

from app.api.deps import get_current_user, require_role
from app.core.exceptions import AppError
from app.core.pagination import parse_pagination
from app.models.prisma_client import get_db
from app.schemas.document import (
    SignRequestResponse,
    to_document_response,
    to_sign_request_response,
)
from app.services.audit_service import log_action
from app.services.notification_service import notify
from app.services.pdf_service import validate_pdf
from app.services.storage_service import upload_file

router = APIRouter(tags=["documents"])

OrgOnly = Annotated[dict[str, Any], Depends(require_role("ORG_ADMIN"))]


@router.post("/documents", status_code=201, response_model=dict)
async def upload_document(
    user: OrgOnly,
    db: Annotated[Prisma, Depends(get_db)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form(min_length=1, max_length=200)],
    description: Annotated[str | None, Form()] = None,
    metadata: Annotated[str, Form()] = "{}",
):
    content = await file.read()
    file_hash = validate_pdf(content, file.filename or "dokumen.pdf")
    try:
        meta = json.loads(metadata) if metadata else {}
        if not isinstance(meta, dict):
            raise ValueError
    except ValueError:
        raise AppError("INVALID_METADATA", "Metadata harus JSON object.", status=400) from None
    path = f"{user['id']}/{uuid.uuid4().hex}.pdf"
    try:
        upload_file(path, content)
    except Exception as exc:
        raise AppError("STORAGE_ERROR", "Gagal menyimpan file.", status=500) from exc
    doc = await db.document.create(
        data={
            "uploaderId": user["id"],
            "title": title,
            "description": description,
            "storagePath": path,
            "fileHash": file_hash,
            "metadata": Json(meta),
            "status": "DRAFT",
        }
    )
    await log_action(db, "UPLOAD", actor_id=user["id"], entity="document", entity_id=doc.id)
    return to_document_response(doc)


@router.get("/documents", response_model=dict)
async def list_documents(
    user: OrgOnly,
    db: Annotated[Prisma, Depends(get_db)],
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
):
    page, limit = parse_pagination(page, limit)
    where: dict[str, Any] = {"uploaderId": user["id"]}
    if status is not None:
        if status not in ("DRAFT", "PENDING", "SIGNED", "REJECTED"):
            raise AppError("INVALID_STATUS", "Status tidak dikenal.", status=400)
        where["status"] = status
    total = await db.document.count(where=where)
    docs = await db.document.find_many(
        where=where, order={"createdAt": "desc"}, skip=(page - 1) * limit, take=limit
    )
    return {
        "data": [to_document_response(d) for d in docs],
        "page": page,
        "limit": limit,
        "total": total,
    }


@router.get("/documents/{id}", response_model=dict)
async def get_document(
    id: str,
    current: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Prisma, Depends(get_db)],
):
    doc = await db.document.find_unique(where={"id": id})
    if doc is None:
        raise AppError("NOT_FOUND", "Dokumen tidak ditemukan.", status=404)
    allowed = doc.uploaderId == current["id"] or current["role"] == "SUPER_ADMIN"
    if not allowed:
        req = await db.signrequest.find_first(
            where={"documentId": id, "signerId": current["id"]}
        )
        allowed = req is not None
    if not allowed:
        raise AppError("NOT_FOUND", "Dokumen tidak ditemukan.", status=404)
    return to_document_response(doc)


@router.post("/documents/{id}/request-sign", status_code=201, response_model=SignRequestResponse,
             response_model_by_alias=True)
async def request_sign(
    id: str,
    payload: dict[str, Any],
    user: OrgOnly,
    db: Annotated[Prisma, Depends(get_db)],
):
    doc = await db.document.find_unique(where={"id": id})
    if doc is None or doc.uploaderId != user["id"]:
        raise AppError("NOT_FOUND", "Dokumen tidak ditemukan.", status=404)
    signer_id = payload.get("signerId", "")
    message = payload.get("message")
    signer = await db.user.find_unique(where={"id": signer_id}) if signer_id else None
    if signer is None or str(signer.role) != "SIGNER":
        raise AppError("INVALID_SIGNER", "Signer tidak valid (harus role SIGNER).", status=400)
    existing = await db.signrequest.find_unique(
        where={"documentId_signerId": {"documentId": id, "signerId": signer_id}}
    )
    if existing:
        raise AppError("DUPLICATE_REQUEST", "Request untuk signer ini sudah ada.", status=409)
    sr = await db.signrequest.create(
        data={"documentId": id, "signerId": signer_id, "message": message}
    )
    await db.document.update(where={"id": id}, data={"status": "PENDING"})
    await notify(db, signer_id, "SIGN_REQUEST", "Permintaan tanda tangan",
                 f"Dokumen '{doc.title}' menunggu tanda tangan Anda.")
    await log_action(db, "REQUEST_SIGN", actor_id=user["id"], entity="sign_request", entity_id=sr.id)
    return to_sign_request_response(sr)
