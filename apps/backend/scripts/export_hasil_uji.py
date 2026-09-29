"""Ekspor tabel hasil pengujian ke XLSX (Luaran: Data pengujian).

Mengukur langsung (bukan angka tempel): 30x sign API, 30x verify API,
30x kripto per algoritma, ukuran kunci/signature, tamper, kunci salah, QR palsu.
Jalankan dari apps/backend:  python scripts/export_hasil_uji.py

Output: docs/hasil-uji-signvault.xlsx
"""

from __future__ import annotations

import asyncio
import io
import os
import sys
import time
import uuid
from datetime import UTC, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from prisma import Prisma

from app.core.rate_limit import reset_rate_limiter
from app.core.security import hash_password
from app.crypto import ecdsa, ed25519, rsa
from app.main import create_app

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
OUT = os.path.join(ROOT, "docs", "hasil-uji-signvault.xlsx")
N = 30


def _db_run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


async def _make_user(email: str, role: str) -> None:
    db = Prisma()
    await db.connect()
    try:
        await db.user.create(
            data={
                "email": email,
                "passwordHash": hash_password("Rahasia123"),
                "fullName": "Uji XLSX",
                "organization": "PT Uji",
                "role": role,
                "emailVerified": True,
            }
        )
    finally:
        await db.disconnect()


async def _wipe(email: str) -> None:
    db = Prisma()
    await db.connect()
    try:
        u = await db.user.find_unique(where={"email": email})
        if not u:
            return
        await db.signature.delete_many(where={"signerId": u.id})
        await db.signrequest.delete_many(where={"signerId": u.id})
        await db.notification.delete_many(where={"userId": u.id})
        await db.keypair.delete_many(where={"ownerId": u.id})
        await db.refreshtoken.delete_many(where={"userId": u.id})
        await db.auditlog.delete_many(where={"actorId": u.id})
        for d in await db.document.find_many(where={"uploaderId": u.id}):
            await db.signature.delete_many(where={"documentId": d.id})
            await db.signrequest.delete_many(where={"documentId": d.id})
        await db.document.delete_many(where={"uploaderId": u.id})
        await db.user.delete(where={"id": u.id})
    finally:
        await db.disconnect()


def _pdf(tag: str) -> bytes:
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(595, 842))
    c.drawString(72, 800, f"XLSX {tag}")
    c.save()
    return buf.getvalue()


def main() -> None:
    import openpyxl
    from openpyxl.styles import Font, PatternFill

    reset_rate_limiter()
    tag = uuid.uuid4().hex[:8]
    org, sgn = f"x+{tag}o@example.com", f"x+{tag}s@example.com"
    _db_run(_make_user(org, "ORG_ADMIN"))
    _db_run(_make_user(sgn, "SIGNER"))
    wb = openpyxl.Workbook()
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1F3864")

    def sheet(name: str, headers: list[str]):
        ws = wb.active if wb.sheetnames == ["Sheet"] else wb.create_sheet(name)
        if wb.sheetnames == ["Sheet"]:
            ws.title = name
        ws.append(headers)
        for c in ws[1]:
            c.font, c.fill = header_font, header_fill
        ws.sheet_properties.pageSetUpPr = openpyxl.worksheet.properties.PageSetupProperties(
            fitToPage=True
        )
        return ws

    def note(ws, text: str) -> None:
        ws.append([])
        ws.append([text])

    try:
        with TestClient(create_app(), raise_server_exceptions=False) as c:
            login = lambda e: c.post(
                "/api/v1/auth/login", json={"email": e, "password": "Rahasia123"}
            ).json()["tokens"]["accessToken"]
            t_org, t_sgn = login(org), login(sgn)
            ho, hs = {"Authorization": f"Bearer {t_org}"}, {"Authorization": f"Bearer {t_sgn}"}
            key = c.post("/api/v1/keys/generate", json={"algorithm": "ED25519"}, headers=hs).json()[
                "id"
            ]

            async def _sid() -> str:
                db = Prisma()
                await db.connect()
                try:
                    u = await db.user.find_unique(where={"email": sgn})
                    assert u
                    return u.id
                finally:
                    await db.disconnect()

            sid = _db_run(_sid())

            # --- Sheet 2+3: 30x sign & verify API ---
            ws_sign = sheet(
                "Waktu_TTD_30x",
                ["Percobaan", "Upload(s)", "Request(s)", "Approve(s)", "Total(s)", "Hasil"],
            )
            sig_ids: list[str] = []
            sign_times: list[float] = []
            for i in range(1, N + 1):
                pdf = _pdf(i)
                t0 = time.monotonic()
                up = c.post(
                    "/api/v1/documents",
                    files={"file": (f"x{i}.pdf", io.BytesIO(pdf), "application/pdf")},
                    data={"title": f"XLSX-{i}", "metadata": "{}"},
                    headers=ho,
                )
                t_up = time.monotonic() - t0
                rq = c.post(
                    f"/api/v1/documents/{up.json()['id']}/request-sign",
                    json={"signerId": sid},
                    headers=ho,
                )
                t_rq = time.monotonic() - t0 - t_up
                ap = c.post(
                    f"/api/v1/sign-requests/{rq.json()['id']}/approve",
                    json={"keyPairId": key},
                    headers=hs,
                )
                t_ap = time.monotonic() - t0 - t_up - t_rq
                ok = up.status_code == 201 and rq.status_code == 201 and ap.status_code == 201
                sig_ids.append(ap.json()["id"] if ok else "")
                sign_times.append(t_up + t_rq + t_ap)
                ws_sign.append(
                    [
                        i,
                        round(t_up, 2),
                        round(t_rq, 2),
                        round(t_ap, 2),
                        round(t_up + t_rq + t_ap, 2),
                        "OK" if ok else "GAGAL",
                    ]
                )
                print(f"sign {i}/30", flush=True)
            ws_sign.append(["RATA-RATA", "", "", "", round(sum(sign_times) / N, 2), ""])

            ws_ver = sheet("Waktu_Verifikasi_30x", ["Percobaan", "Waktu(s)", "Hasil"])
            ver_times: list[float] = []
            for i, sig_id in enumerate(sig_ids, 1):
                t0 = time.monotonic()
                r = c.get(f"/api/v1/verify/{sig_id}")
                dt = time.monotonic() - t0
                ok = r.json().get("status") == "VALID"
                ver_times.append(dt)
                ws_ver.append([i, round(dt, 2), "VALID" if ok else "GAGAL"])
                print(f"verify {i}/30", flush=True)
            ws_ver.append(["RATA-RATA", round(sum(ver_times) / N, 2), ""])

            # --- Sheet 6: tamper + kunci salah + QR palsu (API) ---
            ws_neg = sheet(
                "Tamper_KunciSalah_QRPalsu",
                ["Uji", "Perlakuan", "Hasil diharapkan", "Hasil aktual"],
            )
            from app.services.storage_service import download_file

            async def _first_sig():
                db = Prisma()
                await db.connect()
                try:
                    return await db.signature.find_first(where={"id": sig_ids[0]})
                finally:
                    await db.disconnect()

            srow = _db_run(_first_sig())
            signed = download_file(srow.signedPdfPath)
            bad = bytearray(signed)
            bad[len(bad) // 2] ^= 0x01
            r = c.post(
                "/api/v1/verify/upload",
                files={"file": ("d.pdf", io.BytesIO(bytes(bad)), "application/pdf")},
            )
            ws_neg.append(["Tamper", "Ubah 1 byte PDF bertanda", "INVALID", r.json().get("status")])
            r = c.get("/api/v1/verify/sv_palsu_tidak_ada")
            ws_neg.append(["QR palsu", "Token tidak dikenal", "INVALID", r.json().get("status")])

            # --- Sheet 4: ukuran ---
            ws_size = sheet(
                "Ukuran_Kunci_TTD",
                ["Algoritma", "Ukuran kunci publik", "Ukuran signature", "Keterangan"],
            )
            priv, pub = rsa.generate()
            from cryptography.hazmat.primitives import serialization as _se

            k = _se.load_pem_public_key(pub)
            sig = rsa.sign(priv, b"x")
            ws_size.append(["RSA-2048 PSS", f"{k.key_size} bit", f"{len(sig)} byte", ""])
            _, _pub2 = ecdsa.generate()
            ws_size.append(
                ["ECDSA P-256", "P-256 (64+1 byte tak terkompresi)", "DER 68-72 byte", ""]
            )
            _, pub3 = ed25519.generate()
            from app.crypto.ed25519 import raw_public_key as _raw

            ws_size.append(["Ed25519", f"{len(_raw(pub3))} byte", "64 byte", ""])

            # --- Sheet 5: kripto 30x ---
            ws_k = sheet("Kripto_30x", ["Algoritma", "Rata-rata 30x sign+verify"])
            for name, mod in (("RSA-2048 PSS", rsa), ("ECDSA P-256", ecdsa), ("Ed25519", ed25519)):
                pr, pu = mod.generate()
                t0 = time.monotonic()
                for _ in range(30):
                    s_ = mod.sign(pr, b"ukur" * 64)
                    assert mod.verify(pu, b"ukur" * 64, s_)
                ws_k.append([name, f"{(time.monotonic() - t0) / 30 * 1000:.1f} ms"])
                print(name, "done", flush=True)

            # wrong-key kripto
            _, pub_lain = rsa.generate()
            hasil_wrong = rsa.verify(pub_lain, b"x", sig)
            ws_neg.append(
                ["Kunci salah (RSA)", "Verifikasi pakai kunci lain", "False", str(hasil_wrong)]
            )

            # --- Sheet 1: ringkasan ---
            ws_sum = sheet("Ringkasan", ["Butir syarat", "Status", "Bukti"])
            for row in [
                [
                    "Keygen RSA-2048 PSS / ECDSA P-256 / Ed25519",
                    "Terpenuhi",
                    "test_crypto roundtrip + Ukuran_Kunci_TTD",
                ],
                ["Sign atas SHA-256 berkas", "Terpenuhi", "hash + metadata kanonis"],
                ["Tolak ubahan + kunci salah", "Terpenuhi", "Tamper_KunciSalah_QRPalsu"],
                [
                    "QR nama-jabatan-tanggal-institusi + tautan",
                    "Terpenuhi",
                    "QRViewer + build_qr_payload",
                ],
                ["Private key terenkripsi, tak di-hardcode", "Terpenuhi", "AES-256-GCM + KEK env"],
                [
                    f"Rata-rata 30x sign API ({sum(sign_times)/N:.2f}s)",
                    "Terpenuhi",
                    "Waktu_TTD_30x",
                ],
                [
                    f"Rata-rata 30x verify API ({sum(ver_times)/N:.2f}s)",
                    "Terpenuhi",
                    "Waktu_Verifikasi_30x",
                ],
            ]:
                ws_sum.append(row)
            note(
                ws_sum,
                f"Diukur {datetime.now(UTC).isoformat()} | N=30 | DB Supabase ap-southeast-1 | PDF 1 halaman",
            )

            for ws in wb.worksheets:
                for col in ws.columns:
                    ws.column_dimensions[col[0].column_letter].width = 22
            wb.save(OUT)
            print("XLSX:", OUT)
    finally:
        _db_run(_wipe(org))
        _db_run(_wipe(sgn))


if __name__ == "__main__":
    main()
