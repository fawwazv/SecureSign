"""QR payload publik: JSON ringkas (mudah dipindai) + link verifikasi.

Kebijakan keamanan: payload dibangun dari ALLOWLIST eksplisit — tidak pernah
berisi private key, password, OTP, IP, info perangkat, atau data internal.
Metadata QR hanya rujukan; keaslian HANYA dari verifikasi kriptografis website.
QR terpindai != dokumen valid.
"""

from __future__ import annotations

import io
import json

import qrcode

from app.core.config import settings

# Batas agar QR tetap mudah dipindai pada ukuran box standar.
MAX_PAYLOAD_CHARS = 300

# Field sensitif yang dilarang muncul (substring, case-insensitive).
FORBIDDEN_SUBSTRINGS = (
    "privatekey",
    "private_key",
    "password",
    "otp",
    "token_secret",
    "192.168.",
    "10.0.",
    "android",
    "iphone",
    "user-agent",
)

QR_SCHEMA_VERSION = 1


def verify_url(sig_id: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}/verify/{sig_id}"


def build_qr_payload(
    *,
    document_id: str,
    sig_id: str,
    signer_name: str,
    signer_position: str | None,
    signer_org: str,
    signed_at: str,
    algorithm: str,
) -> str:
    """Susun payload QR publik (allowlist ketat). Raise ValueError bila
    melebihi batas pindai atau mengandung substring terlarang."""
    payload = {
        "v": QR_SCHEMA_VERSION,
        "doc": document_id,
        "sig": sig_id,
        "name": signer_name,
        "pos": signer_position or "",
        "org": signer_org,
        "at": signed_at,
        "alg": algorithm,
        "url": verify_url(sig_id),
    }
    text = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    if len(text) > MAX_PAYLOAD_CHARS:
        raise ValueError("Payload QR melebihi batas pindai.")
    lowered = text.lower()
    for bad in FORBIDDEN_SUBSTRINGS:
        if bad in lowered:
            raise ValueError("Payload QR mengandung data terlarang.")
    return text


def parse_qr_payload(text: str) -> dict:
    """Parse balik (dipakai test + debug). Raise ValueError bila bukan JSON QR."""
    data = json.loads(text)
    if not isinstance(data, dict) or data.get("v") != QR_SCHEMA_VERSION:
        raise ValueError("Bukan payload QR SignVault.")
    return data


def make_qr_png(payload: str, box_size: int = 8, border: int = 2) -> bytes:
    qr = qrcode.QRCode(box_size=box_size, border=border)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
