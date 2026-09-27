"""Validasi PDF + hash (batas 25 MB, prd.md §19)."""

from __future__ import annotations

from app.core.exceptions import AppError
from app.crypto.hashing import sha256_hex

MAX_PDF_BYTES = 25 * 1024 * 1024
PDF_MAGIC = b"%PDF"


def validate_pdf(content: bytes, filename: str) -> str:
    """Validasi file PDF. Return SHA-256 hex. Raise AppError 400 bila tidak valid."""
    if not content:
        raise AppError("EMPTY_FILE", "File kosong.", status=400)
    if len(content) > MAX_PDF_BYTES:
        raise AppError("FILE_TOO_LARGE", "Ukuran PDF melebihi 25 MB.", status=400)
    if not filename.lower().endswith(".pdf") or not content.startswith(PDF_MAGIC):
        raise AppError("INVALID_PDF", "File harus PDF yang valid.", status=400)
    return sha256_hex(content)
