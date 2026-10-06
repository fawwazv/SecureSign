"""Verifikasi publik tanpa login (F-13/F-14) + audit log (F-15).

Keputusan kontrak: sig_id tak dikenal -> 200 INVALID (satu shape VerifyResult),
bukan 404 — sesuai openapi.yaml yang hanya mendokumentasikan 200.
"""

from __future__ import annotations

import base64
import json
import time
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, UploadFile
from prisma import Prisma

from app.api.deps import require_role
from app.core.exceptions import AppError
from app.core.pagination import parse_pagination
from app.crypto import ed25519
from app.crypto.canonical import signed_message
from app.crypto.hashing import sha256_hex
from app.crypto.key_manager import verify_with
from app.models.prisma_client import get_db
from app.schemas.audit import to_audit_response
from app.services.audit_service import log_action
from app.services.pdf_service import MAX_PDF_BYTES, PDF_MAGIC
from app.services.storage_service import download_file

router = APIRouter(tags=["verify"])

AuditorOnly = Annotated[dict[str, Any], Depends(require_role("SUPER_ADMIN", "SEKRETARIAT"))]


def _invalid(reason: str) -> dict[str, Any]:
    return {"status": "INVALID", "reason": reason}


async def _crypto_valid(db: Prisma, sig: Any, key: Any | None = None) -> tuple[bool, str]:
    """Cek kunci aktif + signature kriptografis. Return (valid, reason).
    PADES: validasi ByteRange via pyHanko atas PDF final. LEGACY: verifikasi
    detached atas hash + metadata kanonis.
    `key` opsional: bila diisi (mode kunci manual), kunci DB tidak dibaca
    kecuali untuk cek revoke."""

    if key is None:
        key = await db.keypair.find_unique(where={"id": sig.keyPairId})
        if key is None:
            return False, "Kunci penandatangan tidak ditemukan."
    if getattr(key, "revoked", False):
        return False, "Kunci penandatangan sudah di-revoke."
    if getattr(sig, "sigFormat", "LEGACY") == "PADES":
        return await _pades_valid(db, sig, key)
    try:
        metadata = json.loads(sig.canonicalMetadata)
        message = signed_message(sig.signedHash, metadata)
        ok = verify_with(
            str(sig.algorithm), key.publicKey, message, base64.b64decode(sig.signatureValue)
        )
    except Exception:  # noqa: BLE001 — data korup = INVALID, bukan 500
        return False, "Signature tidak valid."
    return (True, "") if ok else (False, "Hash / signature tidak cocok (dokumen mungkin diubah).")


async def _pades_valid(db: Prisma, sig: Any, key: Any) -> tuple[bool, str]:
    from app.services.pades import avalidate_pades

    _ = db
    if not sig.signedPdfPath:
        return False, "File bertanda tidak ditemukan."
    try:
        signed_bytes = download_file(sig.signedPdfPath)
    except Exception:  # noqa: BLE001 — file hilang = INVALID
        return False, "File bertanda tidak ditemukan."
    result = await avalidate_pades(signed_bytes, key.publicKey)
    if not result["ok"]:
        return False, result["reason"]
    return True, ""


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
        "signerPosition": getattr(sig, "signerPosition", None),
        "signerOrganization": _signer_org_snapshot(sig, signer),
        "signedAt": str(sig.createdAt),
        "reason": None,
        "auditTrail": await _audit_trail(db, sig),
    }


def _signer_org_snapshot(sig: Any, signer: Any) -> str | None:
    """Institusi penandatangan: snapshot `org` dari QR payload (konsisten
    dengan Jabatan), fallback ke organisasi akun saat ini."""
    try:
        from app.services.qr_service import parse_qr_payload

        org = str((parse_qr_payload(sig.qrPayload) or {}).get("org") or "").strip()
        if org:
            return org
    except Exception:  # noqa: BLE001, S110
        pass
    if signer and str(getattr(signer, "organization", "") or "").strip():
        return str(signer.organization).strip()
    return None


@router.get("/verify/{sig_id}", response_model=dict)
async def verify_by_sig_id(sig_id: str, db: Annotated[Prisma, Depends(get_db)]):
    sig = await db.signature.find_unique(where={"id": sig_id})
    if sig is None:
        return _invalid("Token verifikasi tidak ditemukan.")
    ok, reason = await _crypto_valid(db, sig)
    await log_action(
        db,
        "VERIFY",
        entity="signature",
        entity_id=sig_id,
        details={"method": "sig_id", "result": "VALID" if ok else "INVALID"},
    )
    if not ok:
        return _invalid(reason)
    return await _valid_result(db, sig)


@router.post("/verify/manual-file", response_model=dict)
async def verify_manual_file(
    db: Annotated[Prisma, Depends(get_db)],
    file: Annotated[UploadFile, File()],
    public_key: Annotated[str, Form(alias="publicKey")] = "",
):
    """Verifikasi publik memakai file bertanda + kunci publik tempelan (tanpa login).

    Untuk demo "kunci salah" tanpa token dan tanpa sentuh DB: file sama +
    kunci benar -> VALID; file sama + kunci lain -> INVALID.
    """
    from types import SimpleNamespace

    public_key = (public_key or "").strip()
    content = await file.read()
    if not content or len(content) > MAX_PDF_BYTES or not content.startswith(PDF_MAGIC):
        raise AppError("INVALID_PDF", "File harus PDF valid max 25 MB.", status=400)
    if not public_key:
        raise AppError("MISSING_FIELD", "publicKey wajib diisi.", status=400)
    if len(public_key) > 8000 or "BEGIN PUBLIC KEY" not in public_key:
        await log_action(db, "VERIFY", details={"method": "manual-file", "result": "INVALID"})
        return _invalid("Kunci publik tidak valid (harus PEM public key).")
    digest = sha256_hex(content)
    sig = None
    recent = await db.signature.find_many(order={"createdAt": "desc"}, take=50)
    for cand in recent:
        if not cand.signedPdfPath:
            continue
        try:
            signed_bytes = download_file(cand.signedPdfPath)
        except Exception:  # noqa: BLE001, S112 — file hilang = lewati kandidat ini
            continue
        if sha256_hex(signed_bytes) == digest:
            sig = cand
            break
    if sig is None:
        await log_action(db, "VERIFY", details={"method": "manual-file", "result": "INVALID"})
        return _invalid("Tidak ada tanda tangan yang cocok (dokumen mungkin diubah).")
    db_key = await db.keypair.find_unique(where={"id": sig.keyPairId})
    if db_key is not None and db_key.revoked:
        await log_action(
            db,
            "VERIFY",
            entity="signature",
            entity_id=sig.id,
            details={"method": "manual-file", "result": "INVALID"},
        )
        return _invalid("Kunci penandatangan sudah di-revoke.")
    key = SimpleNamespace(publicKey=public_key, revoked=False)
    ok, reason = await _crypto_valid(db, sig, key=key)
    await log_action(
        db,
        "VERIFY",
        entity="signature",
        entity_id=sig.id,
        details={"method": "manual-file", "result": "VALID" if ok else "INVALID"},
    )
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

    # 1. File = PDF bertanda (wajib mengandung QR) -> cocokkan byte file signed.
    #    Urutan ini penting: hash file asli (signedHash) juga cocok untuk file
    #    yang belum ditempeli QR, jadi file asli TIDAK BOLEH dinyatakan VALID.
    recent = await db.signature.find_many(order={"createdAt": "desc"}, take=50)
    signed_available = False
    for sig in recent:
        if not sig.signedPdfPath:
            continue
        try:
            signed_bytes = download_file(sig.signedPdfPath)
        except Exception:  # noqa: BLE001, S112 — file hilang = lewati kandidat ini
            continue
        signed_available = True
        if sha256_hex(signed_bytes) != digest:
            continue
        ok, reason = await _crypto_valid(db, sig)
        if ok:
            await log_action(
                db,
                "VERIFY",
                entity="signature",
                entity_id=sig.id,
                details={"method": "upload-signed", "result": "VALID"},
            )
            return await _valid_result(db, sig)
        await log_action(
            db,
            "VERIFY",
            entity="signature",
            entity_id=sig.id,
            details={"method": "upload-signed", "result": "INVALID"},
        )
        return _invalid(reason or "Tanda tangan tidak valid (dokumen mungkin diubah).")

    # 2. File = PDF asli (hash cocok dengan signedHash) tapi bukan file bertanda
    #    -> TIDAK VALID: QR tidak ada / dokumen belum ditandatangani.
    candidates = await db.signature.find_many(where={"signedHash": digest}, take=10)
    if candidates:
        if not signed_available:
            reason = "File pembanding bertanda tidak ditemukan di penyimpanan."
        else:
            reason = "Dokumen belum ditandatangani (QR-code tidak ada pada file ini)."
        await log_action(db, "VERIFY", details={"method": "upload-original", "result": "INVALID"})
        return _invalid(reason)

    await log_action(db, "VERIFY", details={"method": "upload", "result": "INVALID"})
    return _invalid("Tidak ada tanda tangan yang cocok (dokumen mungkin diubah).")


BENCHMARK_MIN_ITERATIONS = 30
BENCHMARK_MAX_ITERATIONS = 300


def _stats_ms(samples: list[float]) -> dict[str, float]:
    """Ringkasan avg/min/max dalam milidetik."""
    ms = [s * 1000.0 for s in samples]
    return {"avgMs": sum(ms) / len(ms), "minMs": min(ms), "maxMs": max(ms)}


@router.post("/verify/benchmark", response_model=dict)
async def benchmark_upload(
    file: Annotated[UploadFile, File()],
    iterations: Annotated[int, Form(ge=BENCHMARK_MIN_ITERATIONS, le=BENCHMARK_MAX_ITERATIONS)] = 30,
):
    """Uji performa publik tanpa login: sign + verifikasi Ed25519 atas hash PDF.

    Metodologi (Opsi C): tiap iterasi membangun keypair baru lalu sign
    (waktu digabung sebagai "Sign"), kemudian verifikasi hash + signature.
    Berbeda dari test_perf_kripto_30x bawaan yang mengukur sign murni.
    Tanpa audit log (pengukuran, bukan peristiwa verifikasi).
    """
    content = await file.read()
    if not content or len(content) > MAX_PDF_BYTES or not content.startswith(PDF_MAGIC):
        raise AppError("INVALID_PDF", "File harus PDF valid max 25 MB.", status=400)
    message = sha256_hex(content).encode()
    sign_samples: list[float] = []
    verify_samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        priv_pem, pub_pem = ed25519.generate()
        signature = ed25519.sign(priv_pem, message)
        sign_samples.append(time.perf_counter() - start)
        start = time.perf_counter()
        _ = sha256_hex(content)
        valid = ed25519.verify(pub_pem, message, signature)
        verify_samples.append(time.perf_counter() - start)
        if not valid:
            raise AppError("BENCHMARK_FAILED", "Verifikasi internal gagal.", status=500)
    return {
        "iterations": iterations,
        "results": {
            "sign": {
                "operation": "Sign (Ed25519, termasuk pembangunan kunci)",
                **_stats_ms(sign_samples),
            },
            "verify": {"operation": "Verifikasi (Hash + Signature)", **_stats_ms(verify_samples)},
        },
    }


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
