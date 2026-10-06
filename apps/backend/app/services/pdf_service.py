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


def validate_pdf(content: bytes, filename: str) -> tuple[str, int, float, float]:
    """Validasi file PDF. Return (SHA-256 hex, jumlah halaman, lebar, tinggi
    halaman pertama dalam poin). Raise 400 bila tidak valid."""
    if not content:
        raise AppError("EMPTY_FILE", "File kosong.", status=400)
    if len(content) > MAX_PDF_BYTES:
        raise AppError("FILE_TOO_LARGE", "Ukuran PDF melebihi 25 MB.", status=400)
    if not filename.lower().endswith(".pdf") or not content.startswith(PDF_MAGIC):
        raise AppError("INVALID_PDF", "File harus PDF yang valid.", status=400)
    try:
        reader = PdfReader(io.BytesIO(content))
        if not reader.pages:
            raise ValueError("tanpa halaman")
        pages = len(reader.pages)
        first = reader.pages[0]
        width = float(first.mediabox.width)
        height = float(first.mediabox.height)
        if width <= 0 or height <= 0:
            raise ValueError("dimensi halaman tak valid")
    except Exception as exc:
        raise AppError(
            "INVALID_PDF", "File PDF tidak bisa dibaca (mungkin kompresi tak didukung).", status=400
        ) from exc
    return sha256_hex(content), pages, width, height


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
    c.drawImage(
        ImageReader(io.BytesIO(qr_png)),
        x,
        y,
        width=QR_SIZE_PT,
        height=QR_SIZE_PT,
        preserveAspectRatio=True,
    )
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


def embed_qrs(original: bytes, stamps: list[tuple[bytes, int, float, float, float]]) -> bytes:
    """Tempel banyak QR. Tiap stamp: (qr_png, page_1based, x, y, size)
    dalam fraksi 0..1, origin kiri-atas. Return PDF baru."""
    try:
        reader = PdfReader(io.BytesIO(original))
    except Exception as exc:
        raise AppError("INVALID_PDF", "File PDF tidak bisa dibaca.", status=400) from exc
    if not reader.pages:
        raise AppError("INVALID_PDF", "PDF tidak memiliki halaman.", status=400)
    for qr_png, page_no, fx, fy, fsize in stamps:
        idx = min(max(page_no - 1, 0), len(reader.pages) - 1)
        page = reader.pages[idx]
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        size = max(fsize, 0.02) * min(width, height)
        x = min(max(fx, 0.0), 1.0) * width
        y_top = min(max(fy, 0.0), 1.0) * height
        y = height - y_top - size
        stamp = io.BytesIO()
        c = canvas.Canvas(stamp, pagesize=(width, height))
        c.drawImage(
            ImageReader(io.BytesIO(qr_png)),
            x,
            y,
            width=size,
            height=size,
            preserveAspectRatio=True,
        )
        c.save()
        stamp.seek(0)
        page.merge_page(PdfReader(stamp).pages[0])
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
