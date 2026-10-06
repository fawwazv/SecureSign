"""Endpoint documents — upload/list/detail (Sekretariat) + request-sign."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
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
from app.services.storage_service import download_file, upload_file

router = APIRouter(tags=["documents"])

OrgOnly = Annotated[dict[str, Any], Depends(require_role("SEKRETARIAT", "SUPER_ADMIN"))]

log = logging.getLogger("signvault.documents")


def _is_storage_not_found(exc: Exception) -> bool:
    """Deteksi 'object tidak ada' dari Supabase Storage (pesan bervariasi per versi SDK)."""
    text = f"{type(exc).__name__} {exc}".lower()
    cause = getattr(exc, "__cause__", None)
    if cause is not None:
        text += f" {type(cause).__name__} {cause}".lower()
    return any(
        marker in text
        for marker in ("not found", "nosuchkey", "does not exist", "object not exist", " 404")
    )


# Daftar jenis dokumen — sumber kebenaran tunggal, cermin JENIS_LIST di FE.
DOCUMENT_JENIS = (
    "Lainnya",
    "Peraturan",
    "Instruksi",
    "Surat Edaran",
    "Keputusan",
    "Surat Tugas",
    "Surat Dinas",
    "Surat Undangan",
    "Nota Dinas",
    "Memo",
    "Berita Acara",
    "Surat Keterangan",
    "Surat Pengantar",
    "Laporan",
)


def validate_doc_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """Validasi field standar form unggah. Raise AppError 400 bila langgar."""
    nomor = meta.get("nomor", "")
    if nomor and (not isinstance(nomor, str) or len(nomor) > 50):
        raise AppError("INVALID_METADATA", "metadata.nomor maksimal 50 karakter.", status=400)
    tanggal = meta.get("tanggal", "")
    if tanggal:
        from datetime import date

        if not isinstance(tanggal, str):
            raise AppError("INVALID_METADATA", "metadata.tanggal harus string.", status=400)
        try:
            date.fromisoformat(tanggal)
        except ValueError:
            raise AppError(
                "INVALID_METADATA", "metadata.tanggal harus format YYYY-MM-DD.", status=400
            ) from None
    jenis = meta.get("jenis", "")
    if jenis and jenis not in DOCUMENT_JENIS:
        raise AppError("INVALID_METADATA", "metadata.jenis tidak dikenal.", status=400)
    pengirim = meta.get("pengirim", "")
    if pengirim and (not isinstance(pengirim, str) or len(pengirim) > 100):
        raise AppError("INVALID_METADATA", "metadata.pengirim maksimal 100 karakter.", status=400)
    return meta


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
    file_hash, page_count, page_width, page_height = validate_pdf(
        content, file.filename or "dokumen.pdf"
    )
    try:
        meta = json.loads(metadata) if metadata else {}
    except ValueError:
        raise AppError("INVALID_METADATA", "Metadata harus JSON object.", status=400) from None
    if not isinstance(meta, dict):
        raise AppError("INVALID_METADATA", "Metadata harus JSON object.", status=400)
    meta = validate_doc_metadata(meta)
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
            "pageCount": page_count,
            "pageWidth": page_width,
            "pageHeight": page_height,
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
    doc = await _get_allowed_document(db, id, current)
    return to_document_response(doc)


async def _get_allowed_document(db: Prisma, id: str, current: dict[str, Any]) -> Any:
    """Load dokumen + cek akses (uploader / signer ter-assign / superadmin)."""
    doc = await db.document.find_unique(where={"id": id})
    if doc is None:
        raise AppError("NOT_FOUND", "Dokumen tidak ditemukan.", status=404)
    allowed = doc.uploaderId == current["id"] or current["role"] == "SUPER_ADMIN"
    if not allowed:
        req = await db.signrequest.find_first(where={"documentId": id, "signerId": current["id"]})
        allowed = req is not None
    if not allowed:
        raise AppError("NOT_FOUND", "Dokumen tidak ditemukan.", status=404)
    return doc


@router.get("/documents/{id}/download")
async def download_document(
    id: str,
    current: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[Prisma, Depends(get_db)],
    kind: str = "original",
):
    """Unduh PDF asli / bertanda tangan. Privat: hanya pihak berhak."""
    if kind not in ("original", "signed"):
        raise AppError("INVALID_KIND", "kind harus 'original' atau 'signed'.", status=400)
    doc = await _get_allowed_document(db, id, current)
    if kind == "original":
        path = doc.storagePath
    else:
        sigs = await db.signature.find_many(
            where={"documentId": id}, order={"createdAt": "desc"}, take=1
        )
        if not sigs or not sigs[0].signedPdfPath:
            raise AppError("NOT_SIGNED_YET", "Dokumen belum ditandatangani.", status=404)
        path = sigs[0].signedPdfPath
    try:
        content = download_file(path)
    except Exception as exc:
        log.exception("download gagal doc=%s kind=%s path=%s", id, kind, path)
        if _is_storage_not_found(exc):
            if kind == "signed":
                raise AppError(
                    "SIGNED_FILE_NOT_FOUND",
                    "File bertanda tidak ditemukan di penyimpanan. "
                    "Ajukan tanda tangan ulang untuk membuat file baru.",
                    status=404,
                ) from exc
            raise AppError(
                "FILE_NOT_FOUND",
                "File asli tidak ditemukan di penyimpanan.",
                status=404,
            ) from exc
        raise AppError("STORAGE_ERROR", "Gagal mengunduh file.", status=500) from exc
    if not isinstance(content, (bytes, bytearray)) or not bytes(content).startswith(b"%PDF"):
        log.error(
            "download isi tidak valid doc=%s kind=%s path=%s tipe=%s",
            id,
            kind,
            path,
            type(content).__name__,
        )
        raise AppError("STORAGE_ERROR", "Gagal mengunduh file.", status=500)
    safe_title = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in doc.title)[:80]
    return Response(
        content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{safe_title}.pdf"'},
    )


@router.put("/documents/{id}/qr-placements", response_model=dict)
async def save_qr_placements(
    id: str,
    payload: dict[str, Any],
    user: OrgOnly,
    db: Annotated[Prisma, Depends(get_db)],
):
    """Simpan posisi QR (fraksi 0..1, origin kiri-atas). Hanya pemilik + DRAFT."""
    doc = await db.document.find_unique(where={"id": id})
    if doc is None or doc.uploaderId != user["id"]:
        raise AppError("NOT_FOUND", "Dokumen tidak ditemukan.", status=404)
    if doc.status != "DRAFT":
        raise AppError("NOT_DRAFT", "Posisi QR hanya bisa diubah saat DRAFT.", status=409)
    placements = payload.get("placements", [])
    if not isinstance(placements, list) or len(placements) > 10:
        raise AppError("INVALID_PLACEMENTS", "placements harus list (maks 10).", status=400)
    clean: list[dict[str, Any]] = []
    for p in placements:
        if not isinstance(p, dict):
            raise AppError("INVALID_PLACEMENTS", "Tiap placement harus object.", status=400)
        try:
            page = int(p.get("page", 1))
            x, y, size = float(p.get("x", 0)), float(p.get("y", 0)), float(p.get("size", 0.15))
        except (TypeError, ValueError):
            raise AppError("INVALID_PLACEMENTS", "page/x/y/size harus angka.", status=400) from None
        if page < 1 or page > doc.pageCount:
            raise AppError("INVALID_PLACEMENTS", f"page harus 1..{doc.pageCount}.", status=400)
        if not (0 <= x <= 1 and 0 <= y <= 1) or not (0.02 <= size <= 0.8):
            raise AppError("INVALID_PLACEMENTS", "x/y 0..1, size 0.02..0.8.", status=400)
        clean.append({"page": page, "x": x, "y": y, "size": size})
    updated = await db.document.update(where={"id": id}, data={"qrPlacements": Json(clean)})
    await log_action(
        db,
        "QR_PLACE",
        actor_id=user["id"],
        entity="document",
        entity_id=id,
        details={"count": len(clean)},
    )
    return to_document_response(updated)


@router.post(
    "/documents/{id}/request-sign",
    status_code=201,
    response_model=SignRequestResponse,
    response_model_by_alias=True,
)
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
    await notify(
        db,
        signer_id,
        "SIGN_REQUEST",
        "Permintaan tanda tangan",
        f"Dokumen '{doc.title}' menunggu tanda tangan Anda.",
    )
    await log_action(
        db, "REQUEST_SIGN", actor_id=user["id"], entity="sign_request", entity_id=sr.id
    )
    return to_sign_request_response(sr)
