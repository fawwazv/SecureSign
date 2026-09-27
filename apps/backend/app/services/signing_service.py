"""Logika signing: approve satu request (dipakai single & batch).

Alur: cek kepemilikan -> cek key -> unduh PDF asli -> hash ->
sign(hash+metadata kanonis) -> QR -> PDF ber-QR -> simpan (transaksional
per item) -> notifikasi Org Admin.
"""

from __future__ import annotations

import base64
import secrets
from typing import Any

from prisma import Json

from app.core.exceptions import AppError
from app.crypto.canonical import canonicalize_str, signed_message
from app.crypto.hashing import sha256_hex
from app.crypto.key_manager import sign_with
from app.services.audit_service import log_action
from app.services.notification_service import notify
from app.services.pdf_service import embed_qr
from app.services.qr_service import make_qr_png, verify_url
from app.services.storage_service import download_file, upload_file


def new_sig_id() -> str:
    return "sv_" + secrets.token_urlsafe(16)


async def approve_one(
    db: Any,
    sign_request_id: str,
    signer_id: str,
    key_pair_id: str,
    ip: str | None,
) -> Any:
    """Setujui + tandatangani. Return row Signature. Raise AppError bila gagal."""
    sr = await db.signrequest.find_unique(where={"id": sign_request_id})
    if sr is None or sr.signerId != signer_id:
        raise AppError("NOT_FOUND", "Sign request tidak ditemukan.", status=404)
    if sr.status != "PENDING":
        raise AppError("ALREADY_DECIDED", "Request sudah diputuskan.", status=409)

    key = await db.keypair.find_unique(where={"id": key_pair_id})
    if key is None or key.ownerId != signer_id:
        raise AppError("INVALID_KEY", "Key tidak valid.", status=400)
    if key.revoked:
        raise AppError("KEY_REVOKED", "Key sudah di-revoke.", status=400)

    doc = await db.document.find_unique(where={"id": sr.documentId})
    if doc is None:
        raise AppError("NOT_FOUND", "Dokumen tidak ditemukan.", status=404)
    try:
        original = download_file(doc.storagePath)
    except Exception as exc:
        raise AppError("STORAGE_ERROR", "Gagal mengunduh PDF asli.", status=500) from exc
    file_hash = sha256_hex(original)
    if file_hash != doc.fileHash:
        raise AppError("FILE_CHANGED", "File di storage berubah sejak upload.", status=409)

    metadata = dict(doc.metadata) if isinstance(doc.metadata, dict) else {}
    canonical = canonicalize_str(metadata)
    message = signed_message(file_hash, metadata)
    try:
        signature = sign_with(str(key.algorithm), key.encryptedPrivateKey,
                              key.privateKeyNonce, message)
    except Exception as exc:
        raise AppError("SIGN_FAILED", "Gagal menandatangani.", status=500) from exc

    sig_id = new_sig_id()
    qr_payload = verify_url(sig_id)
    signed_pdf = embed_qr(original, make_qr_png(qr_payload), sig_id)
    signed_path = f"signed/{sig_id}.pdf"
    try:
        upload_file(signed_path, signed_pdf)
    except Exception as exc:
        raise AppError("STORAGE_ERROR", "Gagal menyimpan PDF bertanda.", status=500) from exc

    # Optimistic locking: hanya menang bila version belum berubah.
    locked = await db.document.update_many(
        where={"id": doc.id, "version": doc.version},
        data={"version": doc.version + 1, "status": "SIGNED"},
    )
    if locked == 0:
        raise AppError("VERSION_CONFLICT", "Dokumen berubah saat signing.", status=409)

    sig = await db.signature.create(
        data={
            "id": sig_id,
            "documentId": doc.id,
            "signerId": signer_id,
            "keyPairId": key.id,
            "signRequestId": sr.id,
            "algorithm": str(key.algorithm),
            "signatureValue": base64.b64encode(signature).decode(),
            "signedHash": file_hash,
            "canonicalMetadata": canonical,
            "qrPayload": qr_payload,
            "signedPdfPath": signed_path,
        }
    )
    await db.signrequest.update(where={"id": sr.id}, data={"status": "APPROVED"})
    await notify(db, doc.uploaderId, "SIGNED", "Dokumen ditandatangani",
                 f"'{doc.title}' telah ditandatangani.")
    await log_action(db, "APPROVE", actor_id=signer_id, entity="signature",
                     entity_id=sig_id, ip_address=ip)
    return sig
