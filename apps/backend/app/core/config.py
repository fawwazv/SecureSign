"""Application configuration — dimuat dari apps/backend/.env, divalidasi saat startup.

Aturan: tidak ada secret yang di-hardcode; semua dari environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover
        return
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        load_dotenv(env_path)


_load_dotenv()


def _req(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Environment variable {name} wajib diisi di apps/backend/.env")
    return value


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} harus integer, dapat: {raw!r}") from exc


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    if raw in ("1", "true", "yes", "on"):
        return True
    if raw in ("0", "false", "no", "off"):
        return False
    raise RuntimeError(f"Environment variable {name} harus boolean, dapat: {raw!r}")


@dataclass
class Settings:
    env: str = field(default_factory=lambda: os.getenv("ENV", "development"))
    api_base_url: str = field(
        default_factory=lambda: os.getenv("API_BASE_URL", "http://localhost:8000")
    )
    frontend_url: str = field(
        default_factory=lambda: os.getenv("FRONTEND_URL", "http://localhost:5173")
    )

    database_url: str = field(default_factory=lambda: _req("DATABASE_URL"))
    direct_url: str = field(default_factory=lambda: _req("DIRECT_URL"))

    supabase_url: str = field(default_factory=lambda: _req("SUPABASE_URL"))
    supabase_anon_key: str = field(default_factory=lambda: _req("SUPABASE_ANON_KEY"))
    supabase_service_role_key: str = field(
        default_factory=lambda: _req("SUPABASE_SERVICE_ROLE_KEY")
    )
    supabase_jwks_url: str = field(default_factory=lambda: os.getenv("SUPABASE_JWKS_URL", ""))

    jwt_secret: str = field(default_factory=lambda: _req("JWT_SECRET"))
    jwt_refresh_secret: str = field(default_factory=lambda: _req("JWT_REFRESH_SECRET"))
    jwt_access_expire_minutes: int = field(
        default_factory=lambda: _int("JWT_ACCESS_EXPIRE_MINUTES", 15)
    )
    jwt_refresh_expire_days: int = field(default_factory=lambda: _int("JWT_REFRESH_EXPIRE_DAYS", 7))

    kek_secret: str = field(default_factory=lambda: _req("KEK_SECRET"))

    argon2_memory: int = field(default_factory=lambda: _int("ARGON2_MEMORY", 65536))
    argon2_iterations: int = field(default_factory=lambda: _int("ARGON2_ITERATIONS", 3))
    argon2_parallelism: int = field(default_factory=lambda: _int("ARGON2_PARALLELISM", 4))

    rate_limit_per_minute: int = field(default_factory=lambda: _int("RATE_LIMIT_PER_MINUTE", 60))

    google_client_id: str = field(default_factory=lambda: os.getenv("GOOGLE_CLIENT_ID", "").strip())
    google_client_secret: str = field(default_factory=lambda: os.getenv("GOOGLE_CLIENT_SECRET", ""))
    google_allowed_hd: str = field(
        default_factory=lambda: os.getenv("GOOGLE_ALLOWED_HD", "").strip()
    )
    captcha_provider: str = field(
        default_factory=lambda: os.getenv("CAPTCHA_PROVIDER", "turnstile").strip().lower()
    )
    captcha_secret_key: str = field(default_factory=lambda: os.getenv("CAPTCHA_SECRET_KEY", ""))
    captcha_site_key: str = field(default_factory=lambda: os.getenv("CAPTCHA_SITE_KEY", "").strip())
    captcha_enabled: bool = field(default_factory=lambda: _bool("CAPTCHA_ENABLED", False))
    auth_google_rate_per_min: int = field(
        default_factory=lambda: _int("AUTH_GOOGLE_RATE_PER_MIN", 10)
    )
    auth_register_rate_per_min: int = field(
        default_factory=lambda: _int("AUTH_REGISTER_RATE_PER_MIN", 10)
    )

    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", "").strip())
    smtp_port: int = field(default_factory=lambda: _int("SMTP_PORT", 587))
    smtp_user: str = field(default_factory=lambda: os.getenv("SMTP_USER", "").strip())
    smtp_pass: str = field(default_factory=lambda: os.getenv("SMTP_PASS", ""))
    smtp_from: str = field(default_factory=lambda: os.getenv("SMTP_FROM", "").strip())

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_pass)

    @property
    def smtp_sender(self) -> str:
        return self.smtp_from or self.smtp_user

    @property
    def is_dev(self) -> bool:
        return self.env.lower() == "development"

    def __post_init__(self) -> None:
        if (
            self.env.lower() == "production"
            and self.captcha_enabled
            and not self.captcha_secret_key
        ):
            raise RuntimeError("CAPTCHA_ENABLED=true di production mewajibkan CAPTCHA_SECRET_KEY.")
        if self.google_client_secret and not self.google_client_id:
            raise RuntimeError("GOOGLE_CLIENT_SECRET diisi tanpa GOOGLE_CLIENT_ID.")


settings = Settings()
