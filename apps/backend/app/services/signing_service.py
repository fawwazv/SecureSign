"""Logika signing: approve satu request (dipakai single & batch).

Alur: cek kepemilikan -> cek key -> unduh PDF asli -> hash ->
sign(hash+metadata kanonis) -> QR -> PDF ber-QR -> simpan (transaksional
per item) -> notifikasi Sekretariat.
"""

from __future__ import annotations

import base64
import logging
import secrets
from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import AppError
from app.crypto.canonical import canonicalize_str, signed_message
from app.crypto.hashing import sha256_hex
from app.crypto.key_manager import decrypt_private, sign_with
from app.services.audit_service import log_action
from app.services.notification_service import notify
from app.services.pdf_service import embed_qr, embed_qrs
from app.services.qr_service import build_qr_payload, make_qr_png
from app.services.storage_service import download_file, upload_file


def new_sig_id() -> str:
    return "sv_" + secrets.token_urlsafe(16)


log = logging.getLogger("signvault.signing")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


async def approve_one(
    db: Any,
    sign_request_id: str,
    signer_id: str,
    key_pair_id: str,
    ip: str | None,
    position: str | None = None,
) -> Any:
    """Setujui + tandatangani. `position` = jabatan saat signing (opsional).
    Return row Signature. Raise AppError bila gagal."""
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
        signature = sign_with(
            str(key.algorithm), key.encryptedPrivateKey, key.privateKeyNonce, message
        )
    except Exception as exc:
        raise AppError("SIGN_FAILED", "Gagal menandatangani.", status=500) from exc

    sig_id = new_sig_id()
    signer_user = await db.user.find_unique(where={"id": signer_id})
    signer_name = signer_user.fullName if signer_user else signer_id
    signer_org = (signer_user.organization or "") if signer_user else ""
    position = (position or "").strip()[:100] or None
    try:
        qr_payload = build_qr_payload(
            document_id=doc.id,
            sig_id=sig_id,
            signer_name=signer_name,
            signer_position=position,
            signer_org=signer_org,
            signed_at=_now_iso(),
            algorithm=str(key.algorithm),
        )
    except ValueError as exc:
        raise AppError("QR_PAYLOAD_INVALID", str(exc), status=400) from exc
    qr_png = make_qr_png(qr_payload)
    placements = doc.qrPlacements if isinstance(doc.qrPlacements, list) else []
    if placements:
        stamps = [
            (
                qr_png,
                int(p.get("page", 1)),
                float(p.get("x", 0.8)),
                float(p.get("y", 0.8)),
                float(p.get("size", 0.15)),
            )
            for p in placements
            if isinstance(p, dict)
        ]
        qr_base = embed_qrs(original, stamps) if stamps else embed_qr(original, qr_png, sig_id)
    else:
        qr_base = embed_qr(original, qr_png, sig_id)

    # Jalur PAdES: RSA/ECDSA + sertifikat -> ByteRange + appearance di box pertama.
    # Ed25519 / tanpa sertifikat -> legacy detached.
    sig_format = "LEGACY"
    byte_range = ""
    signature_value = base64.b64encode(signature).decode()
    if str(key.algorithm) in ("RSA_PSS_2048", "ECDSA_P256") and key.certificate:
        try:
            from app.services.pades import sign_pdf_pades

            first = placements[0] if placements else {}
            box = (
                int(first.get("page", 1)) if isinstance(first, dict) else 1,
                float(first.get("x", 0.68)) if isinstance(first, dict) else 0.68,
                float(first.get("y", 0.78)) if isinstance(first, dict) else 0.78,
                float(first.get("size", 0.15)) if isinstance(first, dict) else 0.15,
            )
            signed_pdf, byte_range, cms_b64 = await sign_pdf_pades(
                qr_base,
                private_pem=decrypt_private(key.encryptedPrivateKey, key.privateKeyNonce),
                cert_pem=key.certificate,
                box_frac=box,
                appearance_lines=[
                    f"Ditandatangani: {signer_name}",
                    f"Jabatan: {position}" if position else "Jabatan: -",
                    f"Waktu: {_now_iso()}",
                    f"ID: {sig_id}",
                ],
            )
            sig_format = "PADES"
            if cms_b64:
                signature_value = cms_b64
        except AppError:
            raise
        except Exception as exc:
            log.exception("PAdES gagal untuk %s", sig_id)
            raise AppError("SIGN_FAILED", "Gagal menandatangani PAdES.", status=500) from exc
    else:
        signed_pdf = qr_base
    signed_path = f"signed/{sig_id}.pdf"
    try:
        upload_file(signed_path, signed_pdf)
    except Exception as exc:
        raise AppError("STORAGE_ERROR", "Gagal menyimpan PDF bertanda.", status=500) from exc
    # Verifikasi baca-balik: pastikan file benar-benar persisten sebelum
    # dokumen ditandai SIGNED (gagal cepat saat approve, bukan 500 saat preview).
    try:
        saved = download_file(signed_path)
    except Exception as exc:
        log.exception("verifikasi simpan gagal untuk %s", sig_id)
        raise AppError("STORAGE_ERROR", "Gagal menyimpan PDF bertanda.", status=500) from exc
    if not isinstance(saved, (bytes, bytearray)) or not bytes(saved).startswith(b"%PDF"):
        log.error("verifikasi simpan isi tidak valid untuk %s", sig_id)
        raise AppError("STORAGE_ERROR", "Gagal menyimpan PDF bertanda.", status=500)

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
            "signatureValue": signature_value,
            "signedHash": file_hash,
            "canonicalMetadata": canonical,
            "qrPayload": qr_payload,
            "signedPdfPath": signed_path,
            "sigFormat": sig_format,
            "byteRange": byte_range or None,
            "signerPosition": position,
        }
    )
    await db.signrequest.update(where={"id": sr.id}, data={"status": "APPROVED"})
    await notify(
        db,
        doc.uploaderId,
        "SIGNED",
        "Dokumen ditandatangani",
        f"'{doc.title}' telah ditandatangani.",
    )
    await log_action(
        db, "APPROVE", actor_id=signer_id, entity="signature", entity_id=sig_id, ip_address=ip
    )
    return sig
