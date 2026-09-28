"""Test BE-3 CAPTCHA: mock siteverify, tanpa hit Cloudflare sungguhan."""

from __future__ import annotations

import asyncio

import httpx

from app.core.config import settings
from app.core.exceptions import AppError
from app.services.captcha_service import verify_captcha


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _Client:
    def __init__(self, payload=None, boom: bool = False):
        self._payload = payload
        self._boom = boom

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, *a, **k):
        if self._boom:
            raise httpx.ConnectError("putus")
        return _Resp(self._payload)


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _on(monkeypatch) -> None:
    monkeypatch.setattr(settings, "captcha_enabled", True)
    monkeypatch.setattr(settings, "captcha_secret_key", "secret")
    monkeypatch.setattr(settings, "env", "development")


def test_bypass_saat_nonaktif(monkeypatch) -> None:
    monkeypatch.setattr(settings, "captcha_enabled", False)
    _run(verify_captcha(None, None))  # tidak melempar


def test_bypass_env_test(monkeypatch) -> None:
    monkeypatch.setattr(settings, "captcha_enabled", True)
    monkeypatch.setattr(settings, "env", "test")
    _run(verify_captcha(None, None))


def test_sukses(monkeypatch) -> None:
    _on(monkeypatch)
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _Client({"success": True}))
    _run(verify_captcha("tok", "1.2.3.4"))


def test_token_salah_ditolak(monkeypatch) -> None:
    _on(monkeypatch)
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _Client({"success": False}))
    try:
        _run(verify_captcha("salah", None))
        raise AssertionError("harus ditolak")
    except AppError as e:
        assert e.code == "CAPTCHA_FAILED" and e.status == 400


def test_token_kosong_pesan_sama(monkeypatch) -> None:
    _on(monkeypatch)
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _Client({"success": False}))
    try:
        _run(verify_captcha(None, None))
        raise AssertionError("harus ditolak")
    except AppError as e:
        assert e.code == "CAPTCHA_FAILED"


def test_jaringan_putus_ditolak(monkeypatch) -> None:
    _on(monkeypatch)
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _Client(boom=True))
    try:
        _run(verify_captcha("tok", None))
        raise AssertionError("harus ditolak")
    except AppError as e:
        assert e.code == "CAPTCHA_FAILED"
