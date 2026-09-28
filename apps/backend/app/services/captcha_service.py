"""Verifikasi CAPTCHA Cloudflare Turnstile.

Bypass (return) bila CAPTCHA nonaktif atau ENV=test — agar dev/test lokal
tetap jalan sebelum Site/Secret key tersedia.
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.core.exceptions import AppError

log = logging.getLogger("signvault.captcha")

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
HTTP_TIMEOUT = 5


async def verify_captcha(token: str | None, ip: str | None) -> None:
    """Raise AppError(CAPTCHA_FAILED, 400) bila gagal. Pesan sama untuk
    token kosong vs salah agar tidak membocorkan info."""
    if not settings.captcha_enabled or settings.env.lower() == "test":
        log.debug("CAPTCHA bypass (enabled=%s env=%s)", settings.captcha_enabled, settings.env)
        return
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.post(
                SITEVERIFY_URL,
                data={
                    "secret": settings.captcha_secret_key,
                    "response": token or "",
                    "remoteip": ip or "",
                },
            )
            result = resp.json()
    except Exception as exc:
        log.error("CAPTCHA siteverify error: %s", exc)
        raise AppError("CAPTCHA_FAILED", "Verifikasi CAPTCHA gagal.", status=400) from exc
    if not isinstance(result, dict) or result.get("success") is not True:
        raise AppError("CAPTCHA_FAILED", "Verifikasi CAPTCHA gagal.", status=400)
