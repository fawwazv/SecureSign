"""Test Fase 3: upload/list/detail dokumen, request-sign, pending, notifikasi + RBAC."""

from __future__ import annotations

import asyncio
import io
import uuid

import pytest
from fastapi.testclient import TestClient
from prisma import Prisma

from app.core.rate_limit import reset_rate_limiter
from app.core.security import hash_password
from app.main import create_app

FAKE_PDF = b"%PDF-1.4\n%fake untuk test\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


@pytest.fixture(scope="module")
def client() -> TestClient:
    reset_rate_limiter()
    with TestClient(create_app(), raise_server_exceptions=False) as c:
        yield c


def _make_user(email: str, role: str) -> None:
    async def _go() -> None:
        db = Prisma()
        await db.connect()
        try:
            await db.user.create(
                data={
                    "email": email,
                    "passwordHash": hash_password("Rahasia123"),
                    "fullName": "Doc Tester",
                    "organization": "PT Tes",
                    "role": role,
                    "emailVerified": True,
                }
            )
        finally:
            await db.disconnect()

    asyncio.new_event_loop().run_until_complete(_go())


def _cleanup_user(email: str) -> None:
    async def _go() -> None:
        db = Prisma()
        await db.connect()
        try:
            user = await db.user.find_unique(where={"email": email})
            if user:
                await db.signature.delete_many(where={"signerId": user.id})
                await db.signrequest.delete_many(where={"signerId": user.id})
                await db.notification.delete_many(where={"userId": user.id})
                await db.refreshtoken.delete_many(where={"userId": user.id})
                await db.auditlog.delete_many(where={"actorId": user.id})
                docs = await db.document.find_many(where={"uploaderId": user.id})
                for d in docs:
                    await db.signrequest.delete_many(where={"documentId": d.id})
                await db.document.delete_many(where={"uploaderId": user.id})
                await db.user.delete(where={"id": user.id})
        finally:
            await db.disconnect()

    asyncio.new_event_loop().run_until_complete(_go())


def _login(client: TestClient, email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "Rahasia123"})
    assert res.status_code == 200, res.text
    return res.json()["tokens"]["accessToken"]


@pytest.fixture(scope="module")
def users(client: TestClient) -> dict:
    reset_rate_limiter()
    org = f"d+{uuid.uuid4().hex[:10]}@example.com"
    signer = f"d+{uuid.uuid4().hex[:10]}@example.com"
    _make_user(org, "ORG_ADMIN")
    _make_user(signer, "SIGNER")
    data = {"org": org, "signer": signer,
            "t_org": _login(client, org), "t_signer": _login(client, signer)}
    yield data
    _cleanup_user(org)
    _cleanup_user(signer)


def _upload(client: TestClient, token: str, title: str = "Kontrak K-1",
            content: bytes = FAKE_PDF, filename: str = "kontrak.pdf",
            metadata: str = '{"no": "K-1"}') -> dict:
    files = {"file": (filename, io.BytesIO(content), "application/pdf")}
    res = client.post(
        "/api/v1/documents",
        files=files,
        data={"title": title, "description": "desc", "metadata": metadata},
        headers={"Authorization": f"Bearer {token}"},
    )
    return res


def test_upload_dan_validasi(client: TestClient, users: dict) -> None:
    ok = _upload(client, users["t_org"])
    assert ok.status_code == 201, ok.text
    body = ok.json()
    assert body["title"] == "Kontrak K-1" and body["status"] == "DRAFT"
    assert len(body["fileHash"]) == 64 and body["metadata"] == {"no": "K-1"}
    assert set(body) >= {"id", "storagePath", "fileHash", "version", "createdAt", "updatedAt"}

    bukan_pdf = _upload(client, users["t_org"], filename="a.txt", content=b"hello")
    assert bukan_pdf.status_code == 400

    meta_salah = _upload(client, users["t_org"], metadata="bukan-json")
    assert meta_salah.status_code == 400

    # Signer tidak boleh upload.
    forbidden = _upload(client, users["t_signer"])
    assert forbidden.status_code == 403


def test_list_pagination_dan_filter(client: TestClient, users: dict) -> None:
    for i in range(3):
        r = _upload(client, users["t_org"], title=f"Dok-{i}")
        assert r.status_code == 201, r.text
    page1 = client.get("/api/v1/documents?page=1&limit=2",
                       headers={"Authorization": f"Bearer {users['t_org']}"})
    assert page1.status_code == 200
    b1 = page1.json()
    assert (b1["page"], b1["limit"]) == (1, 2) and len(b1["data"]) == 2 and b1["total"] >= 3
    filt = client.get("/api/v1/documents?status=DRAFT",
                      headers={"Authorization": f"Bearer {users['t_org']}"})
    assert filt.status_code == 200 and all(d["status"] == "DRAFT" for d in filt.json()["data"])
    bad = client.get("/api/v1/documents?status=ANEH",
                     headers={"Authorization": f"Bearer {users['t_org']}"})
    assert bad.status_code == 400


def test_detail_akses(client: TestClient, users: dict) -> None:
    doc_id = _upload(client, users["t_org"]).json()["id"]
    me = client.get(f"/api/v1/documents/{doc_id}",
                    headers={"Authorization": f"Bearer {users['t_org']}"})
    assert me.status_code == 200
    # Signer lain tanpa request -> 404 (tidak bocor).
    other = client.get(f"/api/v1/documents/{doc_id}",
                       headers={"Authorization": f"Bearer {users['t_signer']}"})
    assert other.status_code == 404
    assert client.get(f"/api/v1/documents/{doc_id}").status_code == 401


def test_request_sign_pending_notifikasi(client: TestClient, users: dict) -> None:
    doc_id = _upload(client, users["t_org"], title="Minta Sign").json()["id"]

    async def _signer_id() -> str:
        db = Prisma()
        await db.connect()
        try:
            u = await db.user.find_unique(where={"email": users["signer"]})
            assert u
            return u.id
        finally:
            await db.disconnect()

    sid = asyncio.new_event_loop().run_until_complete(_signer_id())

    # Signer id asal -> 400.
    bad = client.post(f"/api/v1/documents/{doc_id}/request-sign",
                      json={"signerId": "tidak-ada"},
                      headers={"Authorization": f"Bearer {users['t_org']}"})
    assert bad.status_code == 400

    req = client.post(f"/api/v1/documents/{doc_id}/request-sign",
                      json={"signerId": sid, "message": "Mohon tanda tangan"},
                      headers={"Authorization": f"Bearer {users['t_org']}"})
    assert req.status_code == 201, req.text
    assert req.json()["status"] == "PENDING"

    # Duplikat -> 409.
    dup = client.post(f"/api/v1/documents/{doc_id}/request-sign",
                      json={"signerId": sid},
                      headers={"Authorization": f"Bearer {users['t_org']}"})
    assert dup.status_code == 409

    # Dokumen berubah PENDING.
    det = client.get(f"/api/v1/documents/{doc_id}",
                     headers={"Authorization": f"Bearer {users['t_org']}"})
    assert det.json()["status"] == "PENDING"

    # Signer melihat pending + dapat notifikasi.
    pend = client.get("/api/v1/sign-requests/pending",
                      headers={"Authorization": f"Bearer {users['t_signer']}"})
    assert pend.status_code == 200 and pend.json()["total"] >= 1
    notif = client.get("/api/v1/notifications",
                       headers={"Authorization": f"Bearer {users['t_signer']}"})
    assert notif.status_code == 200
    items = notif.json()["data"]
    assert any(n["type"] == "SIGN_REQUEST" for n in items)

    # Org Admin tidak boleh buka pending signer.
    assert client.get("/api/v1/sign-requests/pending",
                      headers={"Authorization": f"Bearer {users['t_org']}"}).status_code == 403
