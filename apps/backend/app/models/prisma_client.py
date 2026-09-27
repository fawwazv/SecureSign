"""Singleton Prisma Client + helper lifespan untuk FastAPI."""

from __future__ import annotations

from prisma import Prisma

_db: Prisma | None = None


def get_db() -> Prisma:
    global _db
    if _db is None:
        _db = Prisma()
    return _db


async def connect_db() -> None:
    await get_db().connect()


async def disconnect_db() -> None:
    global _db
    if _db is not None and _db.is_connected():
        await _db.disconnect()
