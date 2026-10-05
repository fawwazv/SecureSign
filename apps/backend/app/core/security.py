"""Keamanan: Argon2id, JWT access/refresh + rotation, email token.

Parameter Argon2id mengikuti prd.md §8: memori 64MB, 3 iterasi, 4 paralel.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

ALGORITHM = "HS256"
EMAIL_TOKEN_BYTES = 32  # 32-byte random, single-use, expired 24 jam (prd.md §8)

_ph: PasswordHasher | None = None


def password_hasher(
    memory_kb: int = 65536, iterations: int = 3, parallelism: int = 4
) -> PasswordHasher:
    global _ph
    if _ph is None:
        _ph = PasswordHasher(memory_cost=memory_kb, time_cost=iterations, parallelism=parallelism)
    return _ph


def hash_password(password: str) -> str:
    return password_hasher().hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return password_hasher().verify(hashed, password)
    except VerifyMismatchError:
        return False
    except Exception:  # noqa: BLE001 — hash korup / format tak dikenal -> tolak
        return False


def generate_email_token() -> str:
    return secrets.token_urlsafe(EMAIL_TOKEN_BYTES)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hex; token asli tidak pernah disimpan di DB."""
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(user_id: str, role: str, secret: str, expire_minutes: int) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": _now() + timedelta(minutes=expire_minutes),
        "iat": _now(),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def create_refresh_token(user_id: str, secret: str, expire_days: int) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": _now() + timedelta(days=expire_days),
        "iat": _now(),
        # jti acak: dua token dalam detik yang sama harus tetap unik
        # (hash disimpan unique di DB; tanpanya refresh ganda -> 500).
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str, secret: str, expected_type: str) -> dict[str, Any]:
    """Decode + validasi exp dan tipe token. Raise ValueError bila tidak valid."""
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Token tidak valid atau kedaluwarsa.") from exc
    if payload.get("type") != expected_type:
        raise ValueError("Tipe token tidak sesuai.")
    if not payload.get("sub"):
        raise ValueError("Token tidak memuat identitas user.")
    return payload
