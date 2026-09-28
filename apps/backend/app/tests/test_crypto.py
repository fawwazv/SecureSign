"""Test Fase 2: roundtrip 3 algoritma, tamper, wrong-key, ukuran, KEK, kanonis, API RBAC."""

from __future__ import annotations

import asyncio
import base64
import uuid

import pytest
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient
from prisma import Prisma

from app.core.rate_limit import reset_rate_limiter
from app.core.security import hash_password
from app.crypto import ecdsa, ed25519, rsa
from app.crypto.canonical import canonicalize, signed_message
from app.crypto.hashing import sha256_hex
from app.crypto.key_manager import (
    decrypt_private,
    encrypt_private,
    generate_keypair,
    sign_with,
    verify_with,
)
from app.main import create_app

MESSAGE = b"dokumen-contoh"
FILE_HASH = sha256_hex(b"%PDF-fake-bytes")
META = {"title": "Kontrak", "doc": "K-1"}


@pytest.fixture(scope="module")
def client() -> TestClient:
    reset_rate_limiter()
    with TestClient(create_app(), raise_server_exceptions=False) as c:
        yield c


# ---------- unit: roundtrip ----------


def test_rsa_roundtrip_dan_tamper_dan_wrong_key() -> None:
    priv, pub = rsa.generate()
    sig = rsa.sign(priv, MESSAGE)
    assert len(sig) == 256  # RSA-2048 = 256 byte
    assert rsa.verify(pub, MESSAGE, sig) is True
    assert rsa.verify(pub, MESSAGE + b"x", sig) is False  # tamper 1 byte gagal
    _, pub2 = rsa.generate()
    assert rsa.verify(pub2, MESSAGE, sig) is False  # wrong key gagal
    key = serialization.load_pem_public_key(pub)
    assert key.key_size == 2048


def test_ecdsa_roundtrip_dan_tamper_dan_wrong_key() -> None:
    priv, pub = ecdsa.generate()
    sig = ecdsa.sign(priv, MESSAGE)
    assert 68 <= len(sig) <= 72  # DER P-256
    assert ecdsa.verify(pub, MESSAGE, sig) is True
    assert ecdsa.verify(pub, MESSAGE + b"x", sig) is False
    _, pub2 = ecdsa.generate()
    assert ecdsa.verify(pub2, MESSAGE, sig) is False


def test_ed25519_roundtrip_dan_ukuran() -> None:
    priv, pub = ed25519.generate()
    sig = ed25519.sign(priv, MESSAGE)
    assert len(sig) == 64  # prd-backend §6: signature 64 byte
    assert len(ed25519.raw_public_key(pub)) == 32  # public key 32 byte
    assert ed25519.verify(pub, MESSAGE, sig) is True
    assert ed25519.verify(pub, MESSAGE + b"x", sig) is False
    _, pub2 = ed25519.generate()
    assert ed25519.verify(pub2, MESSAGE, sig) is False


def test_kek_encrypt_decrypt_roundtrip() -> None:
    _, priv = rsa.generate()
    enc, nonce = encrypt_private(priv)
    assert decrypt_private(enc, nonce) == priv
    assert enc != base64.b64encode(priv).decode()  # benar-benar terenkripsi


def test_key_manager_tiga_algoritma_dan_algo_salah() -> None:
    for algo in ("RSA_PSS_2048", "ECDSA_P256", "ED25519"):
        pub, enc, nonce = generate_keypair(algo)
        assert pub.startswith("-----BEGIN PUBLIC KEY-----")
        sig = sign_with(algo, enc, nonce, MESSAGE)
        assert verify_with(algo, pub, MESSAGE, sig) is True
        assert verify_with(algo, pub, MESSAGE + b"x", sig) is False
    with pytest.raises(ValueError):
        generate_keypair("DSA_1024")


def test_kanonis_deterministik_dan_signed_message() -> None:
    a = canonicalize({"b": 2, "a": 1})
    b = canonicalize({"a": 1, "b": 2})
    assert a == b == b'{"a":1,"b":2}'
    msg = signed_message(FILE_HASH, META)
    assert msg.startswith(FILE_HASH.encode() + b".")


# ---------- API: RBAC ----------


def _make_verified_user(email: str, role: str) -> None:
    async def _go() -> None:
        db = Prisma()
        await db.connect()
        try:
            await db.user.create(
                data={
                    "email": email,
                    "passwordHash": hash_password("Rahasia123"),
                    "fullName": "Key Tester",
                    "organization": "PT Tes",
                    "role": role,
                    "emailVerified": True,
                }
            )
        finally:
            await db.disconnect()

    asyncio.new_event_loop().run_until_complete(_go())


def _cleanup(email: str) -> None:
    async def _go() -> None:
        db = Prisma()
        await db.connect()
        try:
            user = await db.user.find_unique(where={"email": email})
            if user:
                await db.keypair.delete_many(where={"ownerId": user.id})
                await db.refreshtoken.delete_many(where={"userId": user.id})
                await db.auditlog.delete_many(where={"actorId": user.id})
                await db.user.delete(where={"id": user.id})
        finally:
            await db.disconnect()

    asyncio.new_event_loop().run_until_complete(_go())


def _login(client: TestClient, email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "Rahasia123"})
    assert res.status_code == 200, res.text
    return res.json()["tokens"]["accessToken"]


def test_keys_api_rbac_dan_revoke(client: TestClient) -> None:
    signer = f"k+{uuid.uuid4().hex[:10]}@example.com"
    org = f"k+{uuid.uuid4().hex[:10]}@example.com"
    admin = f"k+{uuid.uuid4().hex[:10]}@example.com"
    for email, role in ((signer, "SIGNER"), (org, "ORG_ADMIN"), (admin, "SUPER_ADMIN")):
        _make_verified_user(email, role)
    try:
        t_signer, t_org, t_admin = (_login(client, e) for e in (signer, org, admin))

        assert (
            client.post("/api/v1/keys/generate", json={"algorithm": "ED25519"}).status_code == 401
        )

        # ORG_ADMIN tidak boleh generate (ikut PRD: Signer only).
        nope = client.post(
            "/api/v1/keys/generate",
            json={"algorithm": "ED25519"},
            headers={"Authorization": f"Bearer {t_org}"},
        )
        assert nope.status_code == 403

        gen = client.post(
            "/api/v1/keys/generate",
            json={"algorithm": "ED25519"},
            headers={"Authorization": f"Bearer {t_signer}"},
        )
        assert gen.status_code == 201, gen.text
        key = gen.json()
        assert key["algorithm"] == "ED25519" and key["revoked"] is False
        assert (
            "encryptedPrivateKey" not in str(key)
            and "private" not in key.get("publicKey", "").lower()
        )
        key_id = key["id"]

        lst = client.get("/api/v1/keys", headers={"Authorization": f"Bearer {t_signer}"})
        assert lst.status_code == 200 and len(lst.json()["data"]) == 1

        # Signer tidak boleh revoke.
        assert (
            client.post(
                f"/api/v1/keys/{key_id}/revoke", headers={"Authorization": f"Bearer {t_signer}"}
            ).status_code
            == 403
        )

        # Revoke key yang tidak ada -> 404.
        assert (
            client.post(
                "/api/v1/keys/tidak-ada/revoke", headers={"Authorization": f"Bearer {t_admin}"}
            ).status_code
            == 404
        )

        rev = client.post(
            f"/api/v1/keys/{key_id}/revoke", headers={"Authorization": f"Bearer {t_admin}"}
        )
        assert rev.status_code == 200
        assert rev.json()["revoked"] is True
    finally:
        for e in (signer, org, admin):
            _cleanup(e)
