"""QR payload = link verifikasi {FRONTEND_URL}/verify/{sig_id}.

Format ini dipahami FE1 (utils/qr.ts: token mentah, path /verify/{token},
atau ?token=). Payload link (bukan full signature) agar QR tetap kecil (PRD §16).
"""

from __future__ import annotations

import io

import qrcode

from app.core.config import settings


def verify_url(sig_id: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}/verify/{sig_id}"


def make_qr_png(payload: str, box_size: int = 8, border: int = 2) -> bytes:
    qr = qrcode.QRCode(box_size=box_size, border=border)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
