"""Seed dev: 4 user (satu per role) untuk unblock FE. Idempoten (upsert per email).

Jalankan dari root repo:  python packages/database/seed.py
Password semua: Dev12345
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend"))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from prisma import Prisma  # noqa: E402

from app.core.security import hash_password  # noqa: E402

USERS = [
    ("superadmin@signvault.dev", "Super Admin", "Platform", "SUPER_ADMIN"),
    ("orgadmin@signvault.dev", "Org Admin", "PT Contoh", "ORG_ADMIN"),
    ("signer@signvault.dev", "Tanda Tangan", "PT Contoh", "SIGNER"),
    ("verifier@signvault.dev", "Verifikator", "Publik", "VERIFIER"),
]


async def main() -> None:
    db = Prisma()
    await db.connect()
    try:
        for email, name, org, role in USERS:
            existing = await db.user.find_unique(where={"email": email})
            if existing:
                print(f"ada: {email} ({role})")
                continue
            await db.user.create(
                data={
                    "email": email,
                    "passwordHash": hash_password("Dev12345"),
                    "fullName": name,
                    "organization": org,
                    "role": role,
                    "emailVerified": True,
                }
            )
            print(f"buat: {email} ({role})")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
