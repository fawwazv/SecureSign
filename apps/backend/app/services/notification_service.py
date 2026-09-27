"""Notifikasi in-app (+ log email dev ke penerima)."""

from __future__ import annotations

from prisma import Prisma


async def notify(
    db: Prisma, user_id: str, notif_type: str, title: str, message: str
) -> None:
    await db.notification.create(
        data={"userId": user_id, "type": notif_type, "title": title, "message": message}
    )
    print(f"[DEV-NOTIF] {notif_type} -> user {user_id}: {title}")
