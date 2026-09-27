"""Supabase Storage (bucket `documents`, private; akses via service role)."""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import settings

BUCKET = "documents"


@lru_cache(maxsize=1)
def get_storage_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def upload_file(path: str, content: bytes, content_type: str = "application/pdf") -> str:
    sb = get_storage_client()
    sb.storage.from_(BUCKET).upload(
        path, content, {"content-type": content_type, "upsert": "true"}
    )
    return path


def download_file(path: str) -> bytes:
    sb = get_storage_client()
    return sb.storage.from_(BUCKET).download(path)


def remove_file(path: str) -> None:
    sb = get_storage_client()
    try:
        sb.storage.from_(BUCKET).remove([path])
    except Exception:
        pass
