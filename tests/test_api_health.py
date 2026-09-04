"""Smoke-тесты FastAPI API."""

import importlib


def test_health_endpoint(monkeypatch):
    """Проверяет, что `/health` возвращает успешный технический статус."""
    monkeypatch.setenv("MAIN_ADMIN_ID", "1")
    monkeypatch.setenv("TG_BOT_TOKEN", "1:test")
    monkeypatch.setenv("TG_BOT_USERNAME", "test_bot")
    monkeypatch.setenv("POSTGRES_USER", "gym")
    monkeypatch.setenv("POSTGRES_PASSWORD", "gym")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_DB", "gym")

    from fastapi.testclient import TestClient

    api_main = importlib.import_module("app.api.main")
    client = TestClient(api_main.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_origins_parse_from_env_string(monkeypatch):
    """Проверяет разбор CORS origins из обычной строки `.env`."""
    monkeypatch.setenv("MAIN_ADMIN_ID", "1")
    monkeypatch.setenv("TG_BOT_TOKEN", "1:test")
    monkeypatch.setenv("TG_BOT_USERNAME", "test_bot")
    monkeypatch.setenv("POSTGRES_USER", "gym")
    monkeypatch.setenv("POSTGRES_PASSWORD", "gym")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_DB", "gym")
    monkeypatch.setenv(
        "BACKEND_CORS_ORIGINS",
        "http://localhost:5173, https://example.com",
    )

    from app.core.config import Settings

    settings = Settings()

    assert settings.backend_cors_origins == [
        "http://localhost:5173",
        "https://example.com",
    ]
