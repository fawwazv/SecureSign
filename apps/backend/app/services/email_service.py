"""Pengiriman email: SMTP bila dikonfigurasi, fallback dev-mode (log link).

Aturan: kegagalan SMTP TIDAK boleh menggagalkan registrasi — user sudah
terbuat dan token tersimpan; link selalu di-log agar bisa dikirim ulang
via /auth/resend-verification.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

log = logging.getLogger("signvault.email")
SMTP_TIMEOUT = 15


def verification_link(email: str, token: str) -> str:
    return f"{settings.frontend_url}/verify-email?email={email}&token={token}"


def send_email(to: str, subject: str, text: str, html: str = "") -> bool:
    """Kirim email via SMTP. Return True bila terkirim (atau dev-mode), False bila gagal."""
    if not settings.smtp_configured:
        log.warning("[DEV-EMAIL] ke %s | %s\n%s", to, subject, text)
        print(f"[DEV-EMAIL] ke {to} | {subject}\n{text}")
        return True
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_sender
    msg["To"] = to
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=SMTP_TIMEOUT) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_pass)
            smtp.send_message(msg)
        log.info("Email terkirim ke %s | %s", to, subject)
        return True
    except Exception as exc:  # noqa: BLE001 — email tak boleh memecahkan flow utama
        log.error("Gagal kirim email ke %s: %s", to, exc)
        return False


def send_verification_email(email: str, token: str) -> str:
    """Kirim email verifikasi. Selalu kembalikan link (untuk log/audit)."""
    link = verification_link(email, token)
    text = (
        f"Halo,\n\nTerima kasih telah mendaftar SignVault.\n"
        f"Verifikasi email Anda dalam 24 jam lewat tautan berikut:\n{link}\n\n"
        f"Tautan hanya sekali pakai. Abaikan email ini jika Anda tidak mendaftar."
    )
    html = (
        f"<p>Halo,</p><p>Terima kasih telah mendaftar <b>SignVault</b>.</p>"
        f'<p><a href="{link}">Klik di sini untuk verifikasi email</a> '
        f"(berlaku 24 jam, sekali pakai).</p>"
        f"<p>Abaikan email ini jika Anda tidak mendaftar.</p>"
    )
    sent = send_email(email, "Verifikasi email SignVault", text, html)
    if not sent:
        # Fallback: cetak link agar akun tetap bisa diverifikasi manual.
        log.warning("[DEV-EMAIL-FALLBACK] verifikasi %s -> %s", email, link)
        print(f"[DEV-EMAIL-FALLBACK] verifikasi {email} -> {link}")
    return link
