"""Test Fase 5: verifikasi publik VALID/INVALID, tamper, fake-QR, revoke, audit RBAC, perf ringkas."""

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
from app.crypto import ecdsa, ed25519, rsa
from app.main import create_app


def _real_pdf_bytes(tag: str = "verify") -> bytes:
    import io as _io

    from reportlab.pdfgen import canvas

    buf = _io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595, 842))
    c.setFont("Helvetica", 12)
    c.drawString(72, 800, f"Dokumen test {tag}")
    c.save()
    return buf.getvalue()


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
                    "fullName": "Verify Tester",
                    "organization": "PT Tes",
                    "role": role,
                    "emailVerified": True,
                }
            )
        finally:
            await db.disconnect()

    _db_run(_go())


def _storage_cleanup(uid: str) -> None:
    from app.services.storage_service import get_storage_client

    sb = get_storage_client()
    for folder in (uid, "signed"):
        for _ in range(2):  # retry 1x lawan flake jaringan
            try:
                entries = sb.storage.from_("documents").list(folder)
                paths = [f"{folder}/{f['name']}" for f in entries if f.get("id")]
                if paths:
                    sb.storage.from_("documents").remove(paths)
                break
            except Exception:  # noqa: BLE001, S110 — cleanup best-effort
                pass


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
        _storage_cleanup(uid)


def _login(client: TestClient, email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "Rahasia123"})
    assert res.status_code == 200, res.text
    return res.json()["tokens"]["accessToken"]


@pytest.fixture(scope="module")
def env(client: TestClient) -> dict:
    reset_rate_limiter()
    org = f"v+{uuid.uuid4().hex[:10]}@example.com"
    signer = f"v+{uuid.uuid4().hex[:10]}@example.com"
    admin = f"v+{uuid.uuid4().hex[:10]}@example.com"
    _make_user(org, "ORG_ADMIN")
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

    # Hapus audit VERIFY tanpa aktor milik run ini.
    async def _wipe() -> None:
        db = Prisma()
        await db.connect()
        try:
            await db.auditlog.delete_many(where={"action": "VERIFY", "actorId": None})
        finally:
            await db.disconnect()

    _db_run(_wipe())


def _signed(client: TestClient, env: dict, title: str) -> tuple[str, bytes, bytes]:
    """Upload -> request -> approve. Return (sig_id, original_pdf, signed_pdf)."""
    pdf = _real_pdf_bytes(title)
    up = client.post(
        "/api/v1/documents",
        files={"file": (f"{title}.pdf", io.BytesIO(pdf), "application/pdf")},
        data={"title": title, "metadata": '{"no": "9"}'},
        headers={"Authorization": f"Bearer {env['t_org']}"},
    )
    assert up.status_code == 201, up.text
    doc_id = up.json()["id"]

    async def _sid() -> str:
        db = Prisma()
        await db.connect()
        try:
            u = await db.user.find_unique(where={"email": env["signer"]})
            assert u
            return u.id
        finally:
            await db.disconnect()

    req = client.post(
        f"/api/v1/documents/{doc_id}/request-sign",
        json={"signerId": _db_run(_sid())},
        headers={"Authorization": f"Bearer {env['t_org']}"},
    )
    assert req.status_code == 201, req.text
    ap = client.post(
        f"/api/v1/sign-requests/{req.json()['id']}/approve",
        json={"keyPairId": env["key_id"]},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert ap.status_code == 201, ap.text
    body = ap.json()
    from app.services.storage_service import download_file

    return body["id"], pdf, download_file(body["signedPdfPath"])


def test_verify_sig_id_valid(client: TestClient, env: dict) -> None:
    sig_id, _, _ = _signed(client, env, "Valid1")
    res = client.get(f"/api/v1/verify/{sig_id}")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "VALID"
    assert body["documentName"] == "Valid1" and body["signerName"] == "Verify Tester"
    assert body["signedAt"] and len(body["auditTrail"]) >= 3


def test_verify_fake_qr_invalid(client: TestClient, env: dict) -> None:
    res = client.get("/api/v1/verify/sv_palsu_tidak_ada")
    assert res.status_code == 200
    assert res.json()["status"] == "INVALID"


def test_verify_upload_original_dan_signed(client: TestClient, env: dict) -> None:
    _, original, signed = _signed(client, env, "Upload1")
    for content in (original, signed):
        res = client.post(
            "/api/v1/verify/upload",
            files={"file": ("dok.pdf", io.BytesIO(content), "application/pdf")},
        )
        assert res.status_code == 200, res.text
        assert res.json()["status"] == "VALID"


def test_verify_tamper_satu_byte_invalid(client: TestClient, env: dict) -> None:
    _, _, signed = _signed(client, env, "Tamper1")
    tampered = bytearray(signed)
    tampered[len(tampered) // 2] ^= 0x01
    res = client.post(
        "/api/v1/verify/upload",
        files={"file": ("dok.pdf", io.BytesIO(bytes(tampered)), "application/pdf")},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "INVALID"


def test_verify_upload_acak_invalid(client: TestClient, env: dict) -> None:
    other = _real_pdf_bytes("asing")
    res = client.post(
        "/api/v1/verify/upload", files={"file": ("dok.pdf", io.BytesIO(other), "application/pdf")}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "INVALID"


def test_verify_signature_db_diubah_invalid(client: TestClient, env: dict) -> None:
    sig_id, _, _ = _signed(client, env, "DbTamper1")

    async def _swap() -> str:
        db = Prisma()
        await db.connect()
        try:
            sig = await db.signature.find_unique(where={"id": sig_id})
            assert sig
            raw = base64.b64decode(sig.signatureValue)
            bad = base64.b64encode(bytes([raw[0] ^ 1]) + raw[1:]).decode()
            await db.signature.update(where={"id": sig_id}, data={"signatureValue": bad})
            return sig.signatureValue
        finally:
            await db.disconnect()

    original_value = _db_run(_swap())
    try:
        res = client.get(f"/api/v1/verify/{sig_id}")
        assert res.json()["status"] == "INVALID"
    finally:

        async def _restore() -> None:
            db = Prisma()
            await db.connect()
            try:
                await db.signature.update(
                    where={"id": sig_id}, data={"signatureValue": original_value}
                )
            finally:
                await db.disconnect()

        _db_run(_restore())


def test_verify_key_revoked_invalid(client: TestClient, env: dict) -> None:
    key = client.post(
        "/api/v1/keys/generate",
        json={"algorithm": "ED25519"},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    ).json()
    pdf = _real_pdf_bytes("Revoke1")
    up = client.post(
        "/api/v1/documents",
        files={"file": ("r.pdf", io.BytesIO(pdf), "application/pdf")},
        data={"title": "Revoke1", "metadata": "{}"},
        headers={"Authorization": f"Bearer {env['t_org']}"},
    )
    doc_id = up.json()["id"]

    async def _sid() -> str:
        db = Prisma()
        await db.connect()
        try:
            u = await db.user.find_unique(where={"email": env["signer"]})
            assert u
            return u.id
        finally:
            await db.disconnect()

    req = client.post(
        f"/api/v1/documents/{doc_id}/request-sign",
        json={"signerId": _db_run(_sid())},
        headers={"Authorization": f"Bearer {env['t_org']}"},
    )
    ap = client.post(
        f"/api/v1/sign-requests/{req.json()['id']}/approve",
        json={"keyPairId": key["id"]},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    sig_id = ap.json()["id"]
    client.post(
        f"/api/v1/keys/{key['id']}/revoke", headers={"Authorization": f"Bearer {env['t_admin']}"}
    )
    res = client.get(f"/api/v1/verify/{sig_id}")
    assert res.json()["status"] == "INVALID"
    assert "revoke" in res.json()["reason"].lower()


def test_audit_logs_rbac(client: TestClient, env: dict) -> None:
    for token in (env["t_admin"], env["t_org"]):
        res = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200, res.text
        body = res.json()
        assert {"data", "page", "limit", "total"} <= set(body)
        assert body["total"] >= 1
    assert (
        client.get(
            "/api/v1/audit-logs", headers={"Authorization": f"Bearer {env['t_signer']}"}
        ).status_code
        == 403
    )
    assert client.get("/api/v1/audit-logs").status_code == 401


def test_perf_kripto_30x_per_algoritma() -> None:
    msg = b"perf" * 256
    for name, mod in (("RSA", rsa), ("ECDSA", ecdsa), ("Ed25519", ed25519)):
        priv, pub = mod.generate()
        start = time.monotonic()
        for _ in range(30):
            sig = mod.sign(priv, msg)
            assert mod.verify(pub, msg, sig)
        avg_ms = (time.monotonic() - start) / 30 * 1000
        print(f"\n{name}: 30x sign+verify avg {avg_ms:.1f} ms")
        assert avg_ms < 1000


def test_perf_api_verify(client: TestClient, env: dict) -> None:
    sig_id, original, _ = _signed(client, env, "Perf1")
    for label, fn in (
        ("GET sig", lambda: client.get(f"/api/v1/verify/{sig_id}")),
        (
            "POST upload",
            lambda: client.post(
                "/api/v1/verify/upload",
                files={"file": ("dok.pdf", io.BytesIO(original), "application/pdf")},
            ),
        ),
    ):
        start = time.monotonic()
        for _ in range(3):
            res = fn()
            assert res.json()["status"] == "VALID"
        avg = (time.monotonic() - start) / 3
        print(f"\n{label}: avg {avg:.2f}s")
        assert avg < 15


def test_verify_pades_rsa_valid_dan_format(client: TestClient, env: dict) -> None:
    """End-to-end PAdES: approve RSA -> GET verify VALID + format tercatat."""
    key = client.post(
        "/api/v1/keys/generate",
        json={"algorithm": "RSA_PSS_2048"},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert key.status_code == 201, key.text
    rsa_key_id = key.json()["id"]

    pdf = _real_pdf_bytes("PadesE2E")
    up = client.post(
        "/api/v1/documents",
        files={"file": ("p.pdf", io.BytesIO(pdf), "application/pdf")},
        data={"title": "PadesE2E", "metadata": "{}"},
        headers={"Authorization": f"Bearer {env['t_org']}"},
    )
    assert up.status_code == 201, up.text

    async def _sid() -> str:
        db = Prisma()
        await db.connect()
        try:
            u = await db.user.find_unique(where={"email": env["signer"]})
            assert u
            return u.id
        finally:
            await db.disconnect()

    req = client.post(
        f"/api/v1/documents/{up.json()['id']}/request-sign",
        json={"signerId": _db_run(_sid())},
        headers={"Authorization": f"Bearer {env['t_org']}"},
    )
    assert req.status_code == 201, req.text
    ap = client.post(
        f"/api/v1/sign-requests/{req.json()['id']}/approve",
        json={"keyPairId": rsa_key_id},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert ap.status_code == 201, ap.text
    assert ap.json()["sigFormat"] == "PADES"
    assert ap.json()["byteRange"]

    res = client.get(f"/api/v1/verify/{ap.json()['id']}")
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "VALID"


def test_perf_api_30x_sign_dan_verify(client: TestClient, env: dict) -> None:
    """Syarat tugas: rata-rata 30x penandatanganan + 30x verifikasi via API."""
    import reportlab.pdfgen.canvas as _C

    async def _sid() -> str:
        db = Prisma()
        await db.connect()
        try:
            u = await db.user.find_unique(where={"email": env["signer"]})
            assert u
            return u.id
        finally:
            await db.disconnect()

    signer_id = _db_run(_sid())
    key = client.post(
        "/api/v1/keys/generate",
        json={"algorithm": "ED25519"},
        headers={"Authorization": f"Bearer {env['t_signer']}"},
    )
    assert key.status_code == 201, key.text
    key_id = key.json()["id"]

    def _pdf(i: int) -> bytes:
        buf = io.BytesIO()
        c = _C.Canvas(buf, pagesize=(595, 842))
        c.drawString(72, 800, f"Perf30-{i}")
        c.save()
        return buf.getvalue()

    sig_ids: list[str] = []
    t0 = time.monotonic()
    for i in range(30):
        pdf = _pdf(i)
        up = client.post(
            "/api/v1/documents",
            files={"file": (f"p{i}.pdf", io.BytesIO(pdf), "application/pdf")},
            data={"title": f"Perf30-{i}", "metadata": "{}"},
            headers={"Authorization": f"Bearer {env['t_org']}"},
        )
        assert up.status_code == 201, up.text
        req = client.post(
            f"/api/v1/documents/{up.json()['id']}/request-sign",
            json={"signerId": signer_id},
            headers={"Authorization": f"Bearer {env['t_org']}"},
        )
        assert req.status_code == 201, req.text
        ap = client.post(
            f"/api/v1/sign-requests/{req.json()['id']}/approve",
            json={"keyPairId": key_id},
            headers={"Authorization": f"Bearer {env['t_signer']}"},
        )
        assert ap.status_code == 201, ap.text
        sig_ids.append(ap.json()["id"])
    sign_avg = (time.monotonic() - t0) / 30
    print(f"\n30x approve API avg {sign_avg:.2f}s")
    assert sign_avg < 15

    t1 = time.monotonic()
    for sig_id in sig_ids:
        res = client.get(f"/api/v1/verify/{sig_id}")
        assert res.json()["status"] == "VALID"
    verify_avg = (time.monotonic() - t1) / 30
    print(f"30x verify API avg {verify_avg:.2f}s")
    assert verify_avg < 15
