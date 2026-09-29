"""Test BE-5 endpoint Google + onboarding (service Google di-mock, DB asli)."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from prisma import Prisma

import app.api.v1.auth as auth_mod
import app.services.captcha_service as cap_mod
from app.core.rate_limit import reset_rate_limiter
from app.core.security import hash_password
from app.main import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    reset_rate_limiter()
    with TestClient(create_app(), raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(autouse=True)
def _no_real_email(monkeypatch) -> None:
    """Cegah pytest mengirim email asli (pernah membanjiri inbox dengan bounce)."""
    monkeypatch.setattr(
        auth_mod,
        "send_verification_email",
        lambda email, token: f"https://test.local/verify-email?email={email}&token={token}",
    )


def _db_run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _fake_claims(sub="g-sub-1", email=None, name="Sinta", picture="https://img/x.png"):
    return {
        "sub": sub,
        "email": email or f"g+{uuid.uuid4().hex[:8]}@example.com",
        "email_verified": True,
        "name": name,
        "picture": picture,
    }


def _mock_google(monkeypatch, claims) -> None:
    monkeypatch.setattr(auth_mod, "verify_google_id_token", lambda tok: claims)


def _cleanup(email: str) -> None:
    async def _go() -> None:
        db = Prisma()
        await db.connect()
        try:
            user = await db.user.find_unique(where={"email": email})
            if user:
                await db.signature.delete_many(where={"signerId": user.id})
                await db.signrequest.delete_many(where={"signerId": user.id})
                await db.notification.delete_many(where={"userId": user.id})
                await db.keypair.delete_many(where={"ownerId": user.id})
                await db.refreshtoken.delete_many(where={"userId": user.id})
                await db.auditlog.delete_many(where={"actorId": user.id})
                await db.document.delete_many(where={"uploaderId": user.id})
                await db.user.delete(where={"id": user.id})
        finally:
            await db.disconnect()

    _db_run(_go())


def test_google_pengguna_baru_belum_lengkap(client: TestClient, monkeypatch) -> None:
    reset_rate_limiter()
    claims = _fake_claims()
    _mock_google(monkeypatch, claims)
    res = client.post("/api/v1/auth/google", json={"idToken": "tok"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["profileCompleted"] is False
    assert body["user"]["authProvider"] == "GOOGLE"
    assert body["user"]["emailVerified"] is True
    assert body["user"]["role"] == "SIGNER"
    assert set(body["tokens"]) == {"accessToken", "refreshToken", "expiresIn"}
    try:
        # Login ulang -> langsung lengkap? belum (belum complete-profile).
        again = client.post("/api/v1/auth/google", json={"idToken": "tok"})
        assert again.json()["profileCompleted"] is False
    finally:
        _cleanup(claims["email"])


def test_onboarding_lengkap_lalu_idempoten_409(client: TestClient, monkeypatch) -> None:
    reset_rate_limiter()
    claims = _fake_claims()
    _mock_google(monkeypatch, claims)
    tokens = client.post("/api/v1/auth/google", json={"idToken": "tok"}).json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['accessToken']}"}
    try:
        me = client.get("/api/v1/users/me", headers=headers).json()
        assert me["profileCompleted"] is False
        done = client.patch(
            "/api/v1/users/me/complete-profile",
            headers=headers,
            json={
                "fullName": "Sinta",
                "organization": "PT Maju",
                "phone": "+628123456789",
                "role": "SEKRETARIAT",
                "purpose": "kerja",
            },
        )
        assert done.status_code == 200, done.text
        assert done.json()["role"] == "SEKRETARIAT"
        assert done.json()["profileCompleted"] is True
        again = client.patch(
            "/api/v1/users/me/complete-profile",
            headers=headers,
            json={
                "fullName": "Sinta",
                "organization": "PT Maju",
                "phone": "+628123456789",
                "role": "SEKRETARIAT",
                "purpose": "kerja",
            },
        )
        assert again.status_code == 409
    finally:
        _cleanup(claims["email"])


def test_google_sub_beda_ditolak(client: TestClient, monkeypatch) -> None:
    reset_rate_limiter()
    claims = _fake_claims(sub="g-sub-A")
    _mock_google(monkeypatch, claims)
    assert client.post("/api/v1/auth/google", json={"idToken": "a"}).status_code == 200
    try:
        monkeypatch.setattr(
            auth_mod,
            "verify_google_id_token",
            lambda tok: _fake_claims(sub="g-sub-B", email=claims["email"]),
        )
        res = client.post("/api/v1/auth/google", json={"idToken": "b"})
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "INVALID_GOOGLE_SUBJECT"
    finally:
        _cleanup(claims["email"])


def test_auto_link_email_ke_google(client: TestClient, monkeypatch) -> None:
    reset_rate_limiter()
    email = f"link+{uuid.uuid4().hex[:8]}@example.com"

    async def _make() -> None:
        db = Prisma()
        await db.connect()
        try:
            await db.user.create(
                data={
                    "email": email,
                    "passwordHash": hash_password("Rahasia123"),
                    "fullName": "Link",
                    "organization": "PT",
                    "role": "SIGNER",
                    "emailVerified": False,
                }
            )
        finally:
            await db.disconnect()

    _db_run(_make())
    try:
        _mock_google(monkeypatch, _fake_claims(sub="g-link-1", email=email))
        res = client.post("/api/v1/auth/google", json={"idToken": "tok"})
        assert res.status_code == 200, res.text
        assert res.json()["user"]["emailVerified"] is True

        async def _linked() -> bool:
            db = Prisma()
            await db.connect()
            try:
                u = await db.user.find_unique(where={"email": email})
                return bool(u and u.googleSub == "g-link-1")
            finally:
                await db.disconnect()

        assert _db_run(_linked())
    finally:
        _cleanup(email)


def test_password_ditolak_untuk_akun_google(client: TestClient, monkeypatch) -> None:
    reset_rate_limiter()
    claims = _fake_claims()
    _mock_google(monkeypatch, claims)
    assert client.post("/api/v1/auth/google", json={"idToken": "tok"}).status_code == 200
    try:
        res = client.post(
            "/api/v1/auth/login", json={"email": claims["email"], "password": "apapun123"}
        )
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "GOOGLE_ACCOUNT_USE_SSO"
    finally:
        _cleanup(claims["email"])


def test_rate_limit_google_10_per_menit(client: TestClient, monkeypatch) -> None:
    reset_rate_limiter()
    claims = _fake_claims()
    _mock_google(monkeypatch, claims)
    try:
        codes = [
            client.post("/api/v1/auth/google", json={"idToken": "t"}).status_code for _ in range(11)
        ]
        assert codes[-1] == 429, codes
        assert codes[0] == 200
    finally:
        _cleanup(claims["email"])


class _Client:
    def __init__(self, ok: bool = True):
        self._ok = ok

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, *a, **k):
        class _R:
            def __init__(self, ok):
                self._ok = ok

            def json(self):
                return {"success": self._ok}

        return _R(self._ok)


class _FakeHttpx:
    def __init__(self, ok: bool = True):
        self._ok = ok

    def AsyncClient(self, *a, **k):
        return _Client(self._ok)


def test_register_captcha_aktif_dan_gagal(client: TestClient, monkeypatch) -> None:
    from app.core.config import settings

    reset_rate_limiter()
    email = f"c+{uuid.uuid4().hex[:10]}@example.com"
    monkeypatch.setattr(settings, "captcha_enabled", True)
    monkeypatch.setattr(settings, "captcha_secret_key", "s")
    try:
        monkeypatch.setattr(cap_mod, "httpx", _FakeHttpx(True))
        ok = client.post(
            "/api/v1/auth/register",
            json={
                "fullName": "Cap Chap",
                "email": email,
                "password": "Rahasia123",
                "organization": "PT Tes",
                "role": "SIGNER",
                "purpose": "uji captcha",
                "captchaToken": "tok",
            },
        )
        assert ok.status_code == 201, ok.text
        email2 = f"c+{uuid.uuid4().hex[:10]}@example.com"
        monkeypatch.setattr(cap_mod, "httpx", _FakeHttpx(False))
        bad = client.post(
            "/api/v1/auth/register",
            json={
                "fullName": "Cap Chap",
                "email": email2,
                "password": "Rahasia123",
                "organization": "PT Tes",
                "role": "SIGNER",
                "purpose": "uji captcha",
                "captchaToken": "salah",
            },
        )
        assert bad.status_code == 400
        assert bad.json()["error"]["code"] == "CAPTCHA_FAILED"
    finally:
        _cleanup(email)
