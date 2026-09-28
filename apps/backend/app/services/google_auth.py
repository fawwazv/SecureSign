"""Verifikasi Google ID Token (GIS) via JWKS, tetap terbitkan JWT internal.

Alur: FE kirim idToken (tombol Google) -> POST /auth/google -> fungsi ini
memvalidasi token ke Google -> klaim dipakai untuk cari/buat user.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import AppError

log = logging.getLogger("signvault.google")

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")
JWKS_TTL_SECONDS = 3600
HTTP_TIMEOUT = 5

_jwks_cache: dict[str, Any] = {"fetched_at": 0.0, "keys": []}


def _fetch_jwks() -> list[dict[str, Any]]:
    now = time.monotonic()
    if now - _jwks_cache["fetched_at"] < JWKS_TTL_SECONDS and _jwks_cache["keys"]:
        return _jwks_cache["keys"]
    try:
        resp = httpx.get(GOOGLE_JWKS_URL, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        keys = resp.json().get("keys", [])
    except Exception as exc:
        raise AppError("GOOGLE_VERIFY_FAILED", "Verifikasi Google gagal.", status=502) from exc
    if not keys:
        raise AppError("GOOGLE_VERIFY_FAILED", "Verifikasi Google gagal.", status=502)
    _jwks_cache.update({"fetched_at": now, "keys": keys})
    return keys


def _find_key(keys: list[dict[str, Any]], kid: str | None) -> dict[str, Any]:
    for key in keys:
        if kid and key.get("kid") == kid:
            return key
    if len(keys) == 1:
        return keys[0]
    raise AppError("INVALID_GOOGLE_TOKEN", "Token Google tidak valid.", status=401)


def verify_google_id_token(id_token: str) -> dict[str, Any]:
    """Validasi id_token. Return klaim {sub, email, email_verified, name, picture, hd}.
    Raise AppError bila tidak valid."""
    if not settings.google_client_id:
        raise AppError("GOOGLE_NOT_CONFIGURED", "Login Google belum dikonfigurasi.", status=503)
    try:
        kid = jwt.get_unverified_header(id_token).get("kid")
    except JWTError as exc:
        raise AppError("INVALID_GOOGLE_TOKEN", "Token Google tidak valid.", status=401) from exc
    key = _find_key(_fetch_jwks(), kid)
    try:
        claims = jwt.decode(
            id_token,
            key,
            algorithms=["RS256"],
            audience=settings.google_client_id,
            issuer=GOOGLE_ISSUERS,
        )
    except JWTError as exc:
        raise AppError("INVALID_GOOGLE_TOKEN", "Token Google tidak valid.", status=401) from exc
    if not claims.get("email"):
        raise AppError("INVALID_GOOGLE_TOKEN", "Token Google tidak memuat email.", status=401)
    if claims.get("email_verified") is not True:
        raise AppError("GOOGLE_EMAIL_NOT_VERIFIED", "Email Google belum terverifikasi.", status=400)
    allowed_hd = settings.google_allowed_hd.strip()
    if allowed_hd and claims.get("hd") != allowed_hd:
        raise AppError("GOOGLE_HD_NOT_ALLOWED", "Domain Google tidak diizinkan.", status=403)
    return claims


def reset_jwks_cache() -> None:
    """Dipakai test."""
    _jwks_cache.update({"fetched_at": 0.0, "keys": []})
