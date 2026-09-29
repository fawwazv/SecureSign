"""Test Fase 1 Auth+RBAC: register -> verify -> login -> refresh(rotation) -> logout.

Memakai DB Supabase asli (pooler). Setiap test memakai email unik dan
membersihkan datanya sendiri agar tidak mengotori database.
"""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from prisma import Prisma

import app.api.v1.auth as auth_mod
import app.services.captcha_service as cap_mod
from app.core.rate_limit import reset_rate_limiter
from app.main import create_app


@pytest.fixture(autouse=True)
def _no_real_email(monkeypatch) -> None:
    """Cegah pytest mengirim email asli (pernah membanjiri inbox dengan bounce)."""
    monkeypatch.setattr(
        auth_mod,
        "send_verification_email",
        lambda email, token: f"https://test.local/verify-email?email={email}&token={token}",
    )


@pytest.fixture(scope="module")
def client() -> TestClient:
    reset_rate_limiter()
    with TestClient(create_app(), raise_server_exceptions=False) as c:
        yield c


class _FakeResp:
    def __init__(self, ok: bool = True):
        self._ok = ok

    def json(self):
        return {"success": self._ok}


class _FakeClient:
    def __init__(self, ok: bool = True):
        self._ok = ok

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, *a, **k):
        return _FakeResp(self._ok)


class _FakeHttpx:
    def __init__(self, ok: bool = True):
        self._ok = ok

    def AsyncClient(self, *a, **k):
        return _FakeClient(self._ok)


def _email() -> str:
    return f"t+{uuid.uuid4().hex[:12]}@example.com"


def _db() -> Prisma:
    db = Prisma()
    asyncio.get_event_loop().run_until_complete(db.connect())
    return db


def _cleanup(email: str) -> None:
    async def _go() -> None:
        db = Prisma()
        await db.connect()
        try:
            user = await db.user.find_unique(where={"email": email})
            if user:
                await db.refreshtoken.delete_many(where={"userId": user.id})
                await db.auditlog.delete_many(where={"actorId": user.id})
                await db.user.delete(where={"id": user.id})
        finally:
            await db.disconnect()

    asyncio.new_event_loop().run_until_complete(_go())


def _register(client: TestClient, email: str, role: str = "SIGNER") -> dict:
    reset_rate_limiter()
    # Mock CAPTCHA agar independen dari setting .env lokal/CI (kunci asli/reject).
    with patch.object(cap_mod, "httpx", _FakeHttpx(True)):
        res = client.post(
            "/api/v1/auth/register",
            json={
                "fullName": "Test User",
                "email": email,
                "password": "Rahasia123",
                "organization": "PT Tes",
                "phone": "+628123456789",
                "role": role,
                "purpose": "testing",
                "captchaToken": "test-bypass",
            },
        )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["phone"] == "+628123456789"
    assert body["authProvider"] == "EMAIL"
    assert body["profileCompleted"] is True
    return body


def _token_from_db(email: str) -> str:
    async def _go() -> str:
        db = Prisma()
        await db.connect()
        try:
            user = await db.user.find_unique(where={"email": email})
            assert user and user.verificationToken
            return str(user.verificationToken)
        finally:
            await db.disconnect()

    return asyncio.new_event_loop().run_until_complete(_go())


def test_register_menolak_role_dan_duplikat(client: TestClient) -> None:
    email = _email()
    try:
        bad = client.post(
            "/api/v1/auth/register",
            json={
                "fullName": "X",
                "email": email,
                "password": "Rahasia123",
                "organization": "PT Tes",
                "role": "SUPER_ADMIN",
                "purpose": "coba",
            },
        )
        assert bad.status_code in (400, 422), bad.text
        _register(client, email)
        with patch.object(cap_mod, "httpx", _FakeHttpx(True)):
            dup = client.post(
                "/api/v1/auth/register",
                json={
                    "fullName": "Yuni",
                    "email": email,
                    "password": "Rahasia123",
                    "organization": "PT Tes",
                    "role": "SIGNER",
                    "purpose": "coba-duplikat",
                },
            )
        assert dup.status_code == 409
        assert dup.json()["error"]["code"] == "EMAIL_TAKEN"
    finally:
        _cleanup(email)


def test_login_ditolak_sebelum_verifikasi(client: TestClient) -> None:
    email = _email()
    try:
        _register(client, email)
        res = client.post("/api/v1/auth/login", json={"email": email, "password": "Rahasia123"})
        assert res.status_code == 403
        assert res.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"
    finally:
        _cleanup(email)


def test_verify_token_salah_ditolak(client: TestClient) -> None:
    email = _email()
    try:
        _register(client, email)
        res = client.post("/api/v1/auth/verify-email", json={"email": email, "token": "salah"})
        assert res.status_code == 400
        assert res.json()["error"]["code"] == "INVALID_TOKEN"
    finally:
        _cleanup(email)


def test_flow_penuh_register_verify_login_me_refresh_logout(client: TestClient) -> None:
    email = _email()
    try:
        user = _register(client, email)
        assert user["emailVerified"] is False
        assert set(user) >= {
            "id",
            "fullName",
            "email",
            "organization",
            "role",
            "emailVerified",
            "createdAt",
        }

        with patch.object(cap_mod, "httpx", _FakeHttpx(True)):
            resend = client.post("/api/v1/auth/resend-verification", json={"email": email})
        assert resend.status_code == 200

        token = _token_from_db(email)
        verify = client.post("/api/v1/auth/verify-email", json={"email": email, "token": token})
        assert verify.status_code == 200, verify.text

        # Token sekali pakai: pakai ulang harus gagal (sudah terverifikasi -> 200 idempoten).
        # Single-use dibuktikan: verificationToken dihapus setelah sukses.
        async def _check_cleared() -> None:
            db = Prisma()
            await db.connect()
            try:
                u = await db.user.find_unique(where={"email": email})
                assert u and u.emailVerified and u.verificationToken is None
            finally:
                await db.disconnect()

        asyncio.new_event_loop().run_until_complete(_check_cleared())

        login = client.post("/api/v1/auth/login", json={"email": email, "password": "Rahasia123"})
        assert login.status_code == 200, login.text
        body = login.json()
        assert set(body["tokens"]) == {"accessToken", "refreshToken", "expiresIn"}
        access, refresh = body["tokens"]["accessToken"], body["tokens"]["refreshToken"]

        me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access}"})
        assert me.status_code == 200
        assert me.json()["email"] == email

        no_auth = client.get("/api/v1/users/me")
        assert no_auth.status_code == 401
        assert set(no_auth.json()["error"]) == {"code", "message"}

        refreshed = client.post("/api/v1/auth/refresh", json={"refreshToken": refresh})
        assert refreshed.status_code == 200, refreshed.text
        new_refresh = refreshed.json()["tokens"]["refreshToken"]

        # Rotation: refresh token lama wajib ditolak.
        reuse = client.post("/api/v1/auth/refresh", json={"refreshToken": refresh})
        assert reuse.status_code == 401

        logout = client.post(
            "/api/v1/auth/logout",
            json={"refreshToken": new_refresh},
            headers={"Authorization": f"Bearer {refreshed.json()['tokens']['accessToken']}"},
        )
        assert logout.status_code == 200

        after_logout = client.post("/api/v1/auth/refresh", json={"refreshToken": new_refresh})
        assert after_logout.status_code == 401
    finally:
        _cleanup(email)


def test_login_password_salah_401(client: TestClient) -> None:
    email = _email()
    try:
        _register(client, email)
        token = _token_from_db(email)
        client.post("/api/v1/auth/verify-email", json={"email": email, "token": token})
        res = client.post("/api/v1/auth/login", json={"email": email, "password": "Salah1234"})
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "INVALID_CREDENTIALS"
    finally:
        _cleanup(email)


def test_list_users_rbac_dan_filter(client: TestClient) -> None:
    org = _email()
    signer = _email()
    try:
        _register(client, org, role="ORG_ADMIN")
        _register(client, signer, role="SIGNER")

        async def _verify(email: str) -> None:
            db = Prisma()
            await db.connect()
            try:
                user = await db.user.find_unique(where={"email": email})
                assert user
                await db.user.update(where={"id": user.id}, data={"emailVerified": True})
            finally:
                await db.disconnect()

        def _login(email: str) -> str:
            res = client.post("/api/v1/auth/login", json={"email": email, "password": "Rahasia123"})
            assert res.status_code == 200, res.text
            return res.json()["tokens"]["accessToken"]

        asyncio.new_event_loop().run_until_complete(_verify(org))
        asyncio.new_event_loop().run_until_complete(_verify(signer))
        t_org, t_signer = _login(org), _login(signer)

        res = client.get("/api/v1/users?role=SIGNER", headers={"Authorization": f"Bearer {t_org}"})
        assert res.status_code == 200, res.text
        body = res.json()
        assert {"data", "page", "limit", "total"} <= set(body)
        assert all(u["role"] == "SIGNER" for u in body["data"])
        assert all("passwordHash" not in u and "verificationToken" not in u for u in body["data"])

        bad_role = client.get(
            "/api/v1/users?role=ANEH", headers={"Authorization": f"Bearer {t_org}"}
        )
        assert bad_role.status_code == 400

        assert (
            client.get("/api/v1/users", headers={"Authorization": f"Bearer {t_signer}"}).status_code
            == 403
        )
        assert client.get("/api/v1/users").status_code == 401
    finally:
        _cleanup(org)
        _cleanup(signer)
