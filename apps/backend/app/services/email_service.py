"""Email mode dev (keputusan terkunci): link verifikasi dicetak ke log server.

Saat SMTP/Supabase siap, ganti fungsi ini tanpa mengubah signature.
"""

from __future__ import annotations

import logging

from app.core.config import settings

log = logging.getLogger("signvault.email")


def verification_link(email: str, token: str) -> str:
    return f"{settings.frontend_url}/verify-email?email={email}&token={token}"


def send_verification_email(email: str, token: str) -> str:
    """Kirim email verifikasi. Mode dev: log + kembalikan link (untuk audit/test manual)."""
    link = verification_link(email, token)
    log.warning("[DEV-EMAIL] verifikasi %s -> %s", email, link)
    print(f"[DEV-EMAIL] verifikasi {email} -> {link}")
    return link
