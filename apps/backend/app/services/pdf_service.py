"""Validasi PDF + hash (batas 25 MB, prd.md §19) + tempel QR ke salinan PDF."""

from __future__ import annotations

import io

from pypdf import PdfReader, PdfWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.core.exceptions import AppError
from app.crypto.hashing import sha256_hex

MAX_PDF_BYTES = 25 * 1024 * 1024
PDF_MAGIC = b"%PDF"
QR_SIZE_PT = 110
QR_MARGIN_PT = 36


def validate_pdf(content: bytes, filename: str) -> str:
    """Validasi file PDF. Return SHA-256 hex. Raise AppError 400 bila tidak valid."""
    if not content:
        raise AppError("EMPTY_FILE", "File kosong.", status=400)
    if len(content) > MAX_PDF_BYTES:
        raise AppError("FILE_TOO_LARGE", "Ukuran PDF melebihi 25 MB.", status=400)
    if not filename.lower().endswith(".pdf") or not content.startswith(PDF_MAGIC):
        raise AppError("INVALID_PDF", "File harus PDF yang valid.", status=400)
    return sha256_hex(content)


def embed_qr(original: bytes, qr_png: bytes, caption: str) -> bytes:
    """Tempel QR (+ caption sig_id) di kanan-bawah halaman terakhir. Return PDF baru."""
    try:
        reader = PdfReader(io.BytesIO(original))
    except Exception as exc:
        raise AppError("INVALID_PDF", "File PDF tidak bisa dibaca.", status=400) from exc
    if not reader.pages:
        raise AppError("INVALID_PDF", "PDF tidak memiliki halaman.", status=400)
    last = reader.pages[-1]
    width = float(last.mediabox.width)
    height = float(last.mediabox.height)

    stamp = io.BytesIO()
    c = canvas.Canvas(stamp, pagesize=(width, height))
    x = width - QR_MARGIN_PT - QR_SIZE_PT
    y = QR_MARGIN_PT + 14
    c.drawImage(ImageReader(io.BytesIO(qr_png)), x, y,
                width=QR_SIZE_PT, height=QR_SIZE_PT, preserveAspectRatio=True)
    c.setFont("Helvetica", 7)
    c.drawString(x, QR_MARGIN_PT, caption[:40])
    c.save()
    stamp.seek(0)

    overlay = PdfReader(stamp).pages[0]
    last.merge_page(overlay)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
