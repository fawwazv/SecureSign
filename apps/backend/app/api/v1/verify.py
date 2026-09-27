"""Verifikasi publik tanpa login (F-13/F-14) + audit log (F-15).

Keputusan kontrak: sig_id tak dikenal -> 200 INVALID (satu shape VerifyResult),
bukan 404 — sesuai openapi.yaml yang hanya mendokumentasikan 200.
"""

from __future__ import annotations

import base64
import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, UploadFile
from prisma import Prisma

from app.api.deps import require_role
from app.core.exceptions import AppError
from app.core.pagination import parse_pagination
from app.crypto.canonical import signed_message
from app.crypto.hashing import sha256_hex
from app.crypto.key_manager import verify_with
from app.models.prisma_client import get_db
from app.schemas.audit import to_audit_response
from app.services.audit_service import log_action
from app.services.pdf_service import MAX_PDF_BYTES, PDF_MAGIC
from app.services.storage_service import download_file

router = APIRouter(tags=["verify"])

AuditorOnly = Annotated[dict[str, Any], Depends(require_role("SUPER_ADMIN", "ORG_ADMIN"))]


def _invalid(reason: str) -> dict[str, Any]:
    return {"status": "INVALID", "reason": reason}


async def _crypto_valid(db: Prisma, sig: Any) -> tuple[bool, str]:
    """Cek kunci aktif + signature kriptografis. Return (valid, reason)."""
    key = await db.keypair.find_unique(where={"id": sig.keyPairId})
    if key is None:
        return False, "Kunci penandatangan tidak ditemukan."
    if key.revoked:
        return False, "Kunci penandatangan sudah di-revoke."
    try:
        metadata = json.loads(sig.canonicalMetadata)
        message = signed_message(sig.signedHash, metadata)
        ok = verify_with(str(sig.algorithm), key.publicKey, message,
                         base64.b64decode(sig.signatureValue))
    except Exception:
        return False, "Signature tidak valid."
    return (True, "") if ok else (False, "Hash / signature tidak cocok (dokumen mungkin diubah).")


async def _audit_trail(db: Prisma, sig: Any) -> list[dict[str, Any]]:
    ids = [sig.id, sig.documentId]
    if sig.signRequestId:
        ids.append(sig.signRequestId)
    logs = await db.auditlog.find_many(
        where={"entityId": {"in": ids}}, order={"createdAt": "asc"}, take=50
    )
    trail: list[dict[str, Any]] = []
    for log in logs:
        actor = "-"
        if log.actorId:
            user = await db.user.find_unique(where={"id": log.actorId})
            if user:
                actor = user.fullName
        trail.append({"event": log.action, "at": str(log.createdAt), "actor": actor})
    return trail


async def _valid_result(db: Prisma, sig: Any) -> dict[str, Any]:
    doc = await db.document.find_unique(where={"id": sig.documentId})
    signer = await db.user.find_unique(where={"id": sig.signerId})
    return {
        "status": "VALID",
        "documentName": doc.title if doc else None,
        "signerName": signer.fullName if signer else None,
        "signedAt": str(sig.createdAt),
        "reason": None,
        "auditTrail": await _audit_trail(db, sig),
    }


@router.get("/verify/{sig_id}", response_model=dict)
async def verify_by_sig_id(sig_id: str, db: Annotated[Prisma, Depends(get_db)]):
    sig = await db.signature.find_unique(where={"id": sig_id})
    if sig is None:
        return _invalid("Token verifikasi tidak ditemukan.")
    ok, reason = await _crypto_valid(db, sig)
    await log_action(db, "VERIFY", entity="signature", entity_id=sig_id,
                     details={"method": "sig_id", "result": "VALID" if ok else "INVALID"})
    if not ok:
        return _invalid(reason)
    return await _valid_result(db, sig)


@router.post("/verify/upload", response_model=dict)
async def verify_upload(
    db: Annotated[Prisma, Depends(get_db)],
    file: Annotated[UploadFile, File()],
):
    content = await file.read()
    if not content or len(content) > MAX_PDF_BYTES or not content.startswith(PDF_MAGIC):
        raise AppError("INVALID_PDF", "File harus PDF valid max 25 MB.", status=400)
    digest = sha256_hex(content)

    # 1. File = PDF asli -> cocokkan signedHash + verifikasi kripto.
    candidates = await db.signature.find_many(where={"signedHash": digest}, take=10)
    for sig in candidates:
        ok, _ = await _crypto_valid(db, sig)
        if ok:
            await log_action(db, "VERIFY", entity="signature", entity_id=sig.id,
                             details={"method": "upload-original", "result": "VALID"})
            return await _valid_result(db, sig)

    # 2. File = PDF bertanda (hash berbeda) -> cocokkan byte file signed.
    recent = await db.signature.find_many(order={"createdAt": "desc"}, take=50)
    for sig in recent:
        if not sig.signedPdfPath:
            continue
        try:
            signed_bytes = download_file(sig.signedPdfPath)
        except Exception:
            continue
        if sha256_hex(signed_bytes) == digest:
            ok, _ = await _crypto_valid(db, sig)
            if ok:
                await log_action(db, "VERIFY", entity="signature", entity_id=sig.id,
                                 details={"method": "upload-signed", "result": "VALID"})
                return await _valid_result(db, sig)

    await log_action(db, "VERIFY", details={"method": "upload", "result": "INVALID"})
    return _invalid("Tidak ada tanda tangan yang cocok (dokumen mungkin diubah).")


audit_router = APIRouter(tags=["audit-logs"])


@audit_router.get("/audit-logs", response_model=dict)
async def list_audit_logs(
    _user: AuditorOnly,
    db: Annotated[Prisma, Depends(get_db)],
    page: int = 1,
    limit: int = 20,
):
    page, limit = parse_pagination(page, limit)
    total = await db.auditlog.count()
    logs = await db.auditlog.find_many(
        order={"createdAt": "desc"}, skip=(page - 1) * limit, take=limit
    )
    return {
        "data": [to_audit_response(a) for a in logs],
        "page": page,
        "limit": limit,
        "total": total,
    }
