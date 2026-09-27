"""Kanonikalisasi JSON subset JCS/RFC 8785 untuk metadata yang ikut ditandatangani.

MVP: sort keys rekursif (json.dumps sort_keys), tanpa whitespace,
UTF-8. Normalisasi angka penuh RFC 8785 di luar scope MVP dan
didokumentasikan di sini agar tidak dianggap lengkap.
"""

from __future__ import annotations

import json
from typing import Any


def canonicalize(metadata: dict[str, Any]) -> bytes:
    return json.dumps(
        metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonicalize_str(metadata: dict[str, Any]) -> str:
    return canonicalize(metadata).decode("utf-8")


def signed_message(file_hash_hex: str, metadata: dict[str, Any]) -> bytes:
    """Payload yang ditandatangani: SHA-256(PDF hex) + '.' + metadata kanonis."""
    return file_hash_hex.encode("utf-8") + b"." + canonicalize(metadata)
