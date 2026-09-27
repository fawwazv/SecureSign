"""Test email: dev-fallback (tanpa SMTP) + path SMTP via mock."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.services import email_service


def test_dev_fallback_tanpa_smtp() -> None:
    assert settings.smtp_configured is False
    link = email_service.send_verification_email("a@example.com", "tok123")
    assert "tok123" in link and "/verify-email?" in link


def test_smtp_terkirim_dengan_mock(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_user", "user@example.com")
    monkeypatch.setattr(settings, "smtp_pass", "secret")
    assert settings.smtp_configured is True
    fake = MagicMock()
    fake.__enter__.return_value = fake
    with patch("smtplib.SMTP", return_value=fake) as smtp_cls:
        ok = email_service.send_email("b@example.com", "Subjek", "Isi", "<p>Isi</p>")
    assert ok is True
    smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=15)
    fake.starttls.assert_called_once()
    fake.login.assert_called_once_with("user@example.com", "secret")
    sent_msg = fake.send_message.call_args[0][0]
    assert sent_msg["To"] == "b@example.com" and sent_msg["Subject"] == "Subjek"


def test_smtp_gagal_tidak_melempar(monkeypatch) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_user", "user@example.com")
    monkeypatch.setattr(settings, "smtp_pass", "secret")
    with patch("smtplib.SMTP", side_effect=OSError("jaringan putus")):
        assert email_service.send_email("c@example.com", "S", "T") is False
        # Verifikasi tetap kembalikan link (fallback) walau SMTP mati.
        link = email_service.send_verification_email("c@example.com", "tok999")
        assert "tok999" in link
