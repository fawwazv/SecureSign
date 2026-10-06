"""Test Fase 4: single approve, batch, reject, key-revoke, verifikasi kriptografis."""

from __future__ import annotations

import asyncio
import base64
import io
import time
import uuid

import pytest
from fastapi.testclient import TestClient
from prisma import Prisma

from app.core.rate_limit import reset_rate_limiter
from app.core.security import hash_password
from app.crypto.canonical import signed_message
from app.crypto.hashing import sha256_hex
from app.crypto.key_manager import verify_with
from app.main import create_app

FAKE_PDF = b"%PDF-1.4\n%fake-sign\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


def _real_pdf_bytes() -> bytes:
    """PDF satu halaman yang valid (bisa di-parse pypdf untuk embed QR)."""
    import io

    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595, 842))
    c.setFont("Helvetica", 12)
    c.drawString(72, 800, "Dokumen test SignVault")
    c.save()
    return buf.getvalue()


REAL_PDF = _real_pdf_bytes()


@pytest.fixture(scope="module")
def client() -> TestClient:
    reset_rate_limiter()
    with TestClient(create_app(), raise_server_exceptions=False) as c:
        yield c


def _db_run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _make_user(email: str, role: str) -> None:
    async def _go() -> None:
        db = Prisma()
        await db.connect()
        try:
            await db.user.create(
                data={
                    "email": email,
                    "passwordHash": hash_password("Rahasia123"),
                    "fullName": "Sign Tester",
                    "organization": "PT Tes",
                    "role": role,
                    "emailVerified": True,
                }
            )
        finally:
            await db.disconnect()

    _db_run(_go())


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
                docs = await db.document.find_many(where={"uploaderId": user.id})
                for d in docs:
                    await db.signature.delete_many(where={"documentId": d.id})
                    await db.signrequest.delete_many(where={"documentId": d.id})
                await db.document.delete_many(where={"uploaderId": user.id})
                await db.user.delete(where={"id": user.id})
                return user.id
        finally:
            await db.disconnect()

    uid = _db_run(_go())
    if uid:
        from app.services.storage_service import get_storage_client

        sb = get_storage_client()
        for folder in (uid, "signed"):
            try:
                entries = sb.storage.from_("documents").list(folder)
                paths = [f"{folder}/{f['name']}" for f in entries if f.get("id")]
                if paths:
                    sb.storage.from_("documents").remove(paths)
            except Exception:  # noqa: BLE001, S110 — cleanup best-effort
                pass


def _login(client: TestClient, email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "Rahasia123"})
    assert res.status_code == 200, res.text
    return res.json()["tokens"]["accessToken"]


@pytest.fixture(scope="module")
def env(client: TestClient) -> dict:
    reset_rate_limiter()
    org = f"s+{uuid.uuid4().hex[:10]}@example.com"
    signer = f"s+{uuid.uuid4().hex[:10]}@example.com"
    admin = f"s+{uuid.uuid4().hex[:10]}@example.com"
    _make_user(org, "SEKRETARIAT")
    _make_user(signer, "SIGNER")
    _make_user(admin, "SUPER_ADMIN")
    data = {
        "org": org,
        "signer": signer,
        "admin": admin,
        "t_org": _login(client, org),
        "t_signer": _login(client, signer),
        "t_admin": _login(client, admin),
    }
    key = client.post(
        "/api/v1/keys/generate",
        json={"algorithm": "ED25519"},
        headers={"Authorization": f"Bearer {data['t_signer']}"},
    )
    assert key.status_code == 201, key.text
    data["key_id"] = key.json()["id"]
    yield data
    for e in (org, signer, admin):
        _cleanup(e)


def _upload(client: TestClient, token: str, title: str) -> str:
    res = client.post(
        "/api/v1/documents",
        files={"file": (f"{title}.pdf", io.BytesIO(REAL_PDF), "application/pdf")},
        data={"title": title, "metadata": '{"no": "1"}'},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _request_sign(client: TestClient, env: dict, doc_id: str) -> str:
    async def _sid() -> str:
        db = Prisma()
        await db.connect()
        try:
            u = await db.user.find_unique(where={"email": env["signer"]})
            assert u
            return u.id
        finally:
            await db.disconnect()

    sid = _db_run(_sid())
    res = client.post(
        f"/api/v1/documents/{doc_id}/request-sign",
        json={"signerId": sid},
        headers={"Authorization": f"Bearer {env['t_org']}"},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_single_approve_end_to_end(client: TestClient, env: dict) -> None:
    doc_id = _upload(client, env["t_org"], "Approve1")
    sr_id = _request_sign(client, env, doc_id)
    start = time.monotonic()
    res = client.post(
        f"/api/v1/sign-requests/{sr_id}/approve",
        json={"keyPairId": env["key_id"]},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    elapsed = time.monotonic() - start
    assert res.status_code == 201, res.text
    sig = res.json()
    assert sig["id"].startswith("sv_") and sig["documentId"] == doc_id
    from app.services.qr_service import parse_qr_payload

    qr = parse_qr_payload(sig["qrPayload"])
    assert qr["sig"] == sig["id"] and qr["url"].endswith(f"/verify/{sig['id']}")
    assert sig["signedPdfPath"] == f"signed/{sig['id']}.pdf"
    print(f"\nsingle-approve: {elapsed:.1f}s")
    assert elapsed < 15

    # Verifikasi kriptografis independen: signature valid atas hash+metadata.
    async def _pubkey() -> str:
        db = Prisma()
        await db.connect()
        try:
            k = await db.keypair.find_unique(where={"id": env["key_id"]})
            assert k
            return k.publicKey
        finally:
            await db.disconnect()

    pub = _db_run(_pubkey())
    msg = signed_message(sha256_hex(REAL_PDF), {"no": "1"})
    assert verify_with("ED25519", pub, msg, base64.b64decode(sig["signatureValue"])) is True

    # PDF bertanda bisa diunduh dan valid.
    from app.services.storage_service import download_file

    signed_pdf = download_file(sig["signedPdfPath"])
    assert signed_pdf.startswith(b"%PDF") and len(signed_pdf) > len(REAL_PDF)

    # Approve ulang -> 409.
    again = client.post(
        f"/api/v1/sign-requests/{sr_id}/approve",
        json={"keyPairId": env["key_id"]},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert again.status_code == 409


def test_batch_approve_campuran(client: TestClient, env: dict) -> None:
    ids = [_request_sign(client, env, _upload(client, env["t_org"], f"Batch{i}")) for i in range(2)]
    res = client.post(
        "/api/v1/sign-requests/batch-approve",
        json={
            "items": [
                {"signRequestId": ids[0], "keyPairId": env["key_id"]},
                {"signRequestId": ids[1], "keyPairId": env["key_id"]},
                {"signRequestId": "tidak-ada", "keyPairId": env["key_id"]},
            ]
        },
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert res.status_code == 200, res.text
    results = {r["signRequestId"]: r for r in res.json()["results"]}
    assert results[ids[0]]["success"] and results[ids[0]]["signatureId"]
    assert results[ids[1]]["success"] and results[ids[1]]["signatureId"]
    assert results["tidak-ada"]["success"] is False
    assert results["tidak-ada"]["error"]["error"]["code"] == "NOT_FOUND"

    empty = client.post(
        "/api/v1/sign-requests/batch-approve",
        json={"items": []},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert empty.status_code == 400


def test_reject_dan_alasan_wajib(client: TestClient, env: dict) -> None:
    sr_id = _request_sign(client, env, _upload(client, env["t_org"], "Tolak1"))
    no_reason = client.post(
        f"/api/v1/sign-requests/{sr_id}/reject",
        json={},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert no_reason.status_code == 400
    rej = client.post(
        f"/api/v1/sign-requests/{sr_id}/reject",
        json={"rejectReason": "Data salah"},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert rej.status_code == 200, rej.text
    body = rej.json()
    assert body["status"] == "REJECTED" and body["rejectReason"] == "Data salah"


def test_approve_key_revoked_ditolak(client: TestClient, env: dict) -> None:
    key = client.post(
        "/api/v1/keys/generate",
        json={"algorithm": "ED25519"},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    ).json()
    client.post(
        f"/api/v1/keys/{key['id']}/revoke", headers={"Authorization": f"Bearer {env['t_admin']}"}
    )
    sr_id = _request_sign(client, env, _upload(client, env["t_org"], "Revoke1"))
    res = client.post(
        f"/api/v1/sign-requests/{sr_id}/approve",
        json={"keyPairId": key["id"]},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "KEY_REVOKED"


def test_embed_qrs_multi_posisi() -> None:
    """Unit murni (tanpa DB): 2 QR posisi custom menempel, halaman tetap."""
    from pypdf import PdfReader

    from app.services.pdf_service import embed_qrs
    from app.services.qr_service import make_qr_png

    original = _real_pdf_bytes()
    qr = make_qr_png("https://localhost:8000/api/v1/verify/sv_test")
    out = embed_qrs(original, [(qr, 1, 0.05, 0.05, 0.25), (qr, 1, 0.7, 0.7, 0.1)])
    assert out.startswith(b"%PDF") and len(out) > len(original)
    assert len(PdfReader(io.BytesIO(out)).pages) == 1


def test_approve_rsa_mencatat_pades(client: TestClient, env: dict) -> None:
    """Approve dengan key RSA -> Signature.format PADES + byteRange terisi."""
    doc_id = _upload(client, env["t_org"], "Pades1")
    sr_id = _request_sign(client, env, doc_id)
    key = client.post(
        "/api/v1/keys/generate",
        json={"algorithm": "RSA_PSS_2048"},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert key.status_code == 201, key.text
    res = client.post(
        f"/api/v1/sign-requests/{sr_id}/approve",
        json={"keyPairId": key.json()["id"]},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["sigFormat"] == "PADES"
    assert body["byteRange"] and len(body["byteRange"].split()) == 4


def test_approve_dengan_jabatan_tersimpan_dan_qr_kaya(client: TestClient, env: dict) -> None:
    """Approve + position -> signerPosition tersimpan + qrPayload JSON terparse."""
    from app.services.qr_service import parse_qr_payload

    doc_id = _upload(client, env["t_org"], "Jabatan1")
    sr_id = _request_sign(client, env, doc_id)
    res = client.post(
        f"/api/v1/sign-requests/{sr_id}/approve",
        json={"keyPairId": env["key_id"], "position": "Direktur Keuangan"},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["signerPosition"] == "Direktur Keuangan"
    data = parse_qr_payload(body["qrPayload"])
    assert data["pos"] == "Direktur Keuangan"
    assert data["doc"] == doc_id and data["sig"] == body["id"]
    assert data["alg"] == "ED25519"

    # Jabatan ikut muncul di hasil verifikasi publik.
    ver = client.get(f"/api/v1/verify/{body['id']}")
    assert ver.status_code == 200, ver.text
    assert ver.json()["status"] == "VALID"
    assert ver.json()["signerPosition"] == "Direktur Keuangan"
    # Institusi: snapshot org dari QR payload (fallback: organisasi akun).
    assert ver.json()["signerOrganization"] == "PT Tes"
