"""Tanda tangan PAdES via pyHanko (RSA-PSS + SHA-256, ByteRange, appearance visual).

Sertifikat self-signed (demo, bukan PSrE). Ed25519 / tanpa sertifikat
tetap memakai jalur detached legacy di signing_service.
"""

from __future__ import annotations

import io
import logging
import tempfile
from typing import Any

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import fields, signers
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.stamp import TextStampStyle
from pypdf import PdfReader

log = logging.getLogger("signvault.pades")

FIELD_PREFIX = "SignVaultSig"


def _page_size(pdf_bytes: bytes, page_1based: int) -> tuple[float, float, int]:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    if not reader.pages:
        raise ValueError("PDF tanpa halaman.")
    idx = min(max(page_1based - 1, 0), len(reader.pages) - 1)
    box = reader.pages[idx].mediabox
    return float(box.width), float(box.height), idx


def fraction_to_box(
    pdf_bytes: bytes, page_1based: int, fx: float, fy: float, fsize: float
) -> tuple[tuple[float, float, float, float], int]:
    """Fraksi (origin kiri-atas) -> box poin PDF (origin kiri-bawah) + index halaman."""
    width, height, idx = _page_size(pdf_bytes, page_1based)
    side = max(fsize, 0.02) * min(width, height)
    x0 = min(max(fx, 0.0), 1.0) * width
    y_top = min(max(fy, 0.0), 1.0) * height
    y0 = max(height - y_top - side, 0.0)
    return (x0, y0, min(x0 + side, width), min(y0 + side, height)), idx


TEXT_BOX_PT = 44.0


def appearance_box_for(
    pdf_bytes: bytes, box_frac: tuple[int, float, float, float] | None
) -> tuple[tuple[float, float, float, float], int]:
    """Box teks appearance: tepat di bawah box QR, clamp dalam halaman.
    Bila tak muat di bawah, pindah ke atas QR."""
    (x0, y0, x1, y1), idx = fraction_to_box(pdf_bytes, *(box_frac or (1, 0.68, 0.78, 0.15)))
    _, height, _ = _page_size(pdf_bytes, (box_frac or (1, 0, 0, 0))[0])
    if y0 - TEXT_BOX_PT >= 0:
        return (x0, y0 - TEXT_BOX_PT, x1, y0), idx
    top = min(y1 + TEXT_BOX_PT, height)
    return (x0, y1, x1, top), idx


async def sign_pdf_pades(
    pdf_bytes: bytes,
    *,
    private_pem: bytes,
    cert_pem: str,
    box_frac: tuple[int, float, float, float] | None,
    appearance_lines: list[str],
    field_name: str = "SignVaultSig1",
) -> tuple[bytes, str, str]:
    """Return (pdf_bertanda, byte_range_str, cms_base64)."""
    import base64

    box, page_idx = appearance_box_for(pdf_bytes, box_frac)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pem") as kf:
        kf.write(private_pem)
        key_path = kf.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pem") as cf:
        cf.write(cert_pem.encode())
        cert_path = cf.name
    try:
        signer = signers.SimpleSigner.load(key_path, cert_path, prefer_pss=True)
        meta = signers.PdfSignatureMetadata(
            field_name=field_name,
            location="Indonesia",
            reason="Tanda tangan digital SignVault",
        )
        writer = IncrementalPdfFileWriter(io.BytesIO(pdf_bytes))
        fields.append_signature_field(writer, SigFieldSpec(field_name, box=box, on_page=page_idx))
        style = TextStampStyle(stamp_text="\n".join(appearance_lines[:5]))
        out = io.BytesIO()
        await signers.PdfSigner(meta, signer=signer, stamp_style=style).async_sign_pdf(
            writer, output=out
        )
    finally:
        import os

        for p in (key_path, cert_path):
            try:
                os.unlink(p)
            except OSError:
                pass
    signed = out.getvalue()
    # Baca ByteRange + CMS dari hasil.
    reader = PdfReader(io.BytesIO(signed))
    vstamp = None
    for pg in reader.pages:
        for annot in pg.get("/Annots") or []:
            v = annot.get_object().get("/V")
            if v is not None:
                vstamp = v
                break
        if vstamp is not None:
            break
    byte_range = " ".join(str(int(x)) for x in (vstamp.get("/ByteRange") if vstamp else []))
    cms_b64 = ""
    try:
        r2 = PdfFileReader(io.BytesIO(signed))
        sigs = list(r2.embedded_signatures)
        if sigs:
            cms_b64 = base64.b64encode(bytes(sigs[0].signed_data.dump())).decode()
    except Exception as exc:  # noqa: BLE001 — record opsional, signature tetap valid
        log.warning("Gagal ekstrak CMS: %s", exc)
    return signed, byte_range, cms_b64


def read_byte_range(signed_pdf: bytes) -> str:
    reader = PdfReader(io.BytesIO(signed_pdf))
    for pg in reader.pages:
        for annot in pg.get("/Annots") or []:
            v = annot.get_object().get("/V")
            if v is not None and v.get("/ByteRange"):
                return " ".join(str(int(x)) for x in v.get("/ByteRange"))
    return ""


def validate_pades(signed_pdf: bytes, public_pem: str) -> dict[str, Any]:
    """Versi sync (boleh dipakai di luar event loop, mis. skrip)."""
    import asyncio

    return asyncio.new_event_loop().run_until_complete(avalidate_pades(signed_pdf, public_pem))


async def avalidate_pades(signed_pdf: bytes, public_pem: str) -> dict[str, Any]:
    """Validasi PAdES: ByteRange utuh + signature valid + sertifikat mengikat
    public key yang tersimpan. Return dict{ok, reason, coverage, signer_cn}.
    Trust chain tidak dipakai (self-signed demo) — identitas di-pin ke DB."""
    from cryptography.hazmat.primitives import serialization
    from pyhanko.pdf_utils.reader import PdfFileReader
    from pyhanko.sign.validation import async_validate_pdf_signature

    try:
        sigs = list(PdfFileReader(io.BytesIO(signed_pdf)).embedded_signatures)
    except Exception:  # noqa: BLE001 — file rusak = INVALID
        return {"ok": False, "reason": "Tidak ada signature PAdES.", "coverage": None}
    if not sigs:
        return {"ok": False, "reason": "Tidak ada signature PAdES.", "coverage": None}
    try:
        status = await async_validate_pdf_signature(sigs[0])
    except Exception:  # noqa: BLE001 — gagal validasi = INVALID
        return {"ok": False, "reason": "Signature tidak valid.", "coverage": None}
    if not (status.valid is True and status.intact is True):
        return {
            "ok": False,
            "reason": "Dokumen berubah setelah ditandatangani.",
            "coverage": str(status.coverage),
        }
    # Pin sertifikat penandatangan ke public key di DB.
    try:
        pub_stored = serialization.load_pem_public_key(public_pem.encode())
        pub_stored = pub_stored.public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        signing_cert = status.signing_cert
        if signing_cert is None:
            return {"ok": False, "reason": "Sertifikat tidak ditemukan.", "coverage": None}
        from asn1crypto import x509 as asn1_x509

        cert_der = signing_cert.dump()
        cert_pub = asn1_x509.Certificate.load(cert_der).public_key.dump()
        from cryptography.hazmat.primitives.serialization import load_der_public_key

        cert_pub_pem = load_der_public_key(cert_pub).public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        if cert_pub_pem != pub_stored:
            return {"ok": False, "reason": "Kunci tidak cocok.", "coverage": None}
        cn = signing_cert.subject.human_friendly
    except Exception:  # noqa: BLE001 — sertifikat rusak = INVALID
        return {"ok": False, "reason": "Sertifikat tidak valid.", "coverage": None}
    return {"ok": True, "reason": "", "coverage": str(status.coverage), "signer_cn": cn}
