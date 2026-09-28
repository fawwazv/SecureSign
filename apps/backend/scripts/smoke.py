"""Smoke test staging (stdlib only): health + register -> verify -> login -> me.

Pakai: ENV=staging python scripts/smoke.py  (backend harus jalan di :8000)
Keluar 0 bila semua lolos, 1 bila ada gagal.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import uuid

BASE = os.getenv("API_BASE_URL", "http://localhost:8000") + "/api/v1"
FAILURES: list[str] = []


def call(method: str, path: str, body: dict | None = None, token: str | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read() or b"{}")
    except Exception as e:  # noqa: BLE001 — smoke: catat, lanjut
        try:
            return getattr(e, "code", "?"), json.loads(e.read() or b"{}")
        except Exception:  # noqa: BLE001 — body non-JSON
            return getattr(e, "code", "?"), {}


def check(label: str, cond: bool, detail: str = "") -> None:
    print(("OK   " if cond else "GAGAL"), label, detail)
    if not cond:
        FAILURES.append(label)


def main() -> int:
    print(f"ENV={os.getenv('ENV', 'development')} BASE={BASE}")
    try:
        with urllib.request.urlopen(BASE.replace("/api/v1", "") + "/health", timeout=10) as r:
            check("health", r.status == 200)
    except Exception as e:  # noqa: BLE001
        check("health", False, str(e)[:80])
        return 1

    email = f"smoke+{uuid.uuid4().hex[:8]}@example.com"
    s, _ = call(
        "POST",
        "/auth/register",
        {
            "fullName": "Smoke",
            "email": email,
            "password": "Rahasia123",
            "organization": "PT",
            "role": "SIGNER",
            "purpose": "smoke",
        },
    )
    check("register-201", s == 201, f"status={s}")

    # Ambil token verifikasi langsung dari DB (mode dev/SMTP apa pun tetap bisa).
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    import asyncio

    from prisma import Prisma

    async def _token() -> str | None:
        db = Prisma()
        await db.connect()
        try:
            u = await db.user.find_unique(where={"email": email})
            return u.verificationToken if u else None
        finally:
            await db.disconnect()

    token = asyncio.run(_token())
    s, _ = call("POST", "/auth/verify-email", {"email": email, "token": token})
    check("verify-200", s == 200, f"status={s}")

    s, b = call("POST", "/auth/login", {"email": email, "password": "Rahasia123"})
    ok = s == 200 and set(b.get("tokens", {})) == {"accessToken", "refreshToken", "expiresIn"}
    check("login-tokens", ok, f"status={s}")
    access = b["tokens"]["accessToken"] if ok else None

    if access:
        s, b = call("GET", "/users/me", token=access)
        check("users-me", s == 200 and b.get("email") == email, f"status={s}")

    async def _wipe() -> None:
        db = Prisma()
        await db.connect()
        try:
            u = await db.user.find_unique(where={"email": email})
            if u:
                await db.refreshtoken.delete_many(where={"userId": u.id})
                await db.auditlog.delete_many(where={"actorId": u.id})
                await db.user.delete(where={"id": u.id})
        finally:
            await db.disconnect()

    asyncio.run(_wipe())
    print("SMOKE:", "LOLOS" if not FAILURES else f"GAGAL {FAILURES}")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    raise SystemExit(main())
