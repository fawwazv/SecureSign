"""Test BE-3 Google: kunci RSA asli, JWKS di-mock, tanpa hit Google sungguhan."""

from __future__ import annotations

import base64
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt

from app.core.config import settings
from app.core.exceptions import AppError
from app.services import google_auth
from app.services.google_auth import reset_jwks_cache, verify_google_id_token

KID = "test-kid-1"


def _b64url_int(n: int) -> str:
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


@pytest.fixture()
def rsa_pair(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = key.public_key().public_numbers()
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": KID,
                "use": "sig",
                "alg": "RS256",
                "n": _b64url_int(pub.n),
                "e": _b64url_int(pub.e),
            }
        ]
    }
    priv_pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    monkeypatch.setattr(settings, "google_client_id", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_allowed_hd", "")
    reset_jwks_cache()

    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return jwks

    monkeypatch.setattr(google_auth.httpx, "get", lambda *a, **k: _Resp())
    return priv_pem


def _token(priv_pem: bytes, **claims) -> str:
    now = int(time.time())
    base = {
        "iss": "https://accounts.google.com",
        "aud": settings.google_client_id,
        "exp": now + 3600,
        "iat": now,
        "sub": "google-sub-123",
        "email": "sinta@mail.id",
        "email_verified": True,
        "name": "Sinta",
        "picture": "https://img/x.png",
    }
    base.update(claims)
    return jwt.encode(base, priv_pem, algorithm="RS256", headers={"kid": KID})


def test_valid(rsa_pair) -> None:
    claims = verify_google_id_token(_token(rsa_pair))
    assert claims["sub"] == "google-sub-123" and claims["email"] == "sinta@mail.id"


def test_wrong_audience_ditolak(rsa_pair) -> None:
    with pytest.raises(AppError) as e:
        verify_google_id_token(_token(rsa_pair, aud="lain.apps.googleusercontent.com"))
    assert e.value.code == "INVALID_GOOGLE_TOKEN" and e.value.status == 401


def test_expired_ditolak(rsa_pair) -> None:
    with pytest.raises(AppError):
        verify_google_id_token(_token(rsa_pair, exp=int(time.time()) - 10))


def test_issuer_salah_ditolak(rsa_pair) -> None:
    with pytest.raises(AppError):
        verify_google_id_token(_token(rsa_pair, iss="https://evil.example.com"))


def test_email_belum_verifikasi_ditolak(rsa_pair) -> None:
    with pytest.raises(AppError) as e:
        verify_google_id_token(_token(rsa_pair, email_verified=False))
    assert e.value.code == "GOOGLE_EMAIL_NOT_VERIFIED"


def test_hd_dibatasi(rsa_pair, monkeypatch) -> None:
    monkeypatch.setattr(settings, "google_allowed_hd", "sekolah.id")
    with pytest.raises(AppError) as e:
        verify_google_id_token(_token(rsa_pair))
    assert e.value.code == "GOOGLE_HD_NOT_ALLOWED"
    claims = verify_google_id_token(_token(rsa_pair, hd="sekolah.id"))
    assert claims["hd"] == "sekolah.id"


def test_token_rusak_ditolak(rsa_pair) -> None:
    with pytest.raises(AppError):
        verify_google_id_token("bukan-jwt")


def test_jaringan_gagal_502(monkeypatch) -> None:
    monkeypatch.setattr(settings, "google_client_id", "test-client-id.apps.googleusercontent.com")
    reset_jwks_cache()

    def _boom(*a, **k):
        raise OSError("putus")

    monkeypatch.setattr(google_auth.httpx, "get", _boom)
    with pytest.raises(AppError) as e:
        verify_google_id_token("x.y.z")
    assert e.value.code in ("INVALID_GOOGLE_TOKEN", "GOOGLE_VERIFY_FAILED")


def test_tanpa_client_id_503(monkeypatch) -> None:
    monkeypatch.setattr(settings, "google_client_id", "")
    reset_jwks_cache()
    with pytest.raises(AppError) as e:
        verify_google_id_token("x.y.z")
    assert e.value.status == 503
