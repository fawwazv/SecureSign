"""Test BE-2: parsing config OAuth/CAPTCHA + validasi startup."""

from __future__ import annotations

import importlib

import pytest

import app.core.config as config_mod


def _reload(monkeypatch, env: dict) -> object:
    # Bekukan dotenv agar reload tidak memuat ulang .env asli (independen env lokal/CI).
    import dotenv

    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    for key in (
        "ENV",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_ALLOWED_HD",
        "CAPTCHA_PROVIDER",
        "CAPTCHA_SECRET_KEY",
        "CAPTCHA_SITE_KEY",
        "CAPTCHA_ENABLED",
        "AUTH_GOOGLE_RATE_PER_MIN",
        "AUTH_REGISTER_RATE_PER_MIN",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return importlib.reload(config_mod)


def test_default_aman_tanpa_kunci(monkeypatch) -> None:
    mod = _reload(monkeypatch, {})
    assert mod.settings.captcha_enabled is False
    assert mod.settings.google_client_id == ""
    assert mod.settings.auth_google_rate_per_min == 10
    assert mod.settings.auth_register_rate_per_min == 10


def test_bool_parsing(monkeypatch) -> None:
    mod = _reload(monkeypatch, {"CAPTCHA_ENABLED": "true"})
    assert mod.settings.captcha_enabled is True
    mod = _reload(monkeypatch, {"CAPTCHA_ENABLED": "0"})
    assert mod.settings.captcha_enabled is False
    with pytest.raises(RuntimeError):
        _reload(monkeypatch, {"CAPTCHA_ENABLED": "mungkin"})


def test_prod_captcha_tanpa_secret_ditolak(monkeypatch) -> None:
    with pytest.raises(RuntimeError):
        _reload(monkeypatch, {"ENV": "production", "CAPTCHA_ENABLED": "true"})
    mod = _reload(
        monkeypatch,
        {"ENV": "production", "CAPTCHA_ENABLED": "true", "CAPTCHA_SECRET_KEY": "s3cr3t"},
    )
    assert mod.settings.captcha_enabled is True


def test_secret_tanpa_client_id_ditolak(monkeypatch) -> None:
    with pytest.raises(RuntimeError):
        _reload(monkeypatch, {"GOOGLE_CLIENT_SECRET": "shhh"})
