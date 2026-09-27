"""Test fondasi Langkah 1: health, format error, proteksi auth, CORS."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.rate_limit import reset_rate_limiter
from app.main import create_app


def _client() -> TestClient:
    reset_rate_limiter()
    return TestClient(create_app(), raise_server_exceptions=False)


def test_health_ok() -> None:
    assert _client().get("/health").json() == {"status": "ok"}


def test_openapi_terbit() -> None:
    res = _client().get("/openapi.json")
    assert res.status_code == 200
    assert res.json()["info"]["title"] == "SignVault API"


def test_404_format_error_disepakati() -> None:
    res = _client().get("/api/v1/tidak-ada")
    assert res.status_code == 404
    body = res.json()
    assert set(body["error"]) == {"code", "message"}


def test_cors_hanya_domain_fe() -> None:
    res = _client().options(
        "/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_rate_limit_60_per_menit() -> None:
    client = _client()
    statuses = [client.get("/api/v1/tidak-ada").status_code for _ in range(65)]
    assert 429 in statuses
