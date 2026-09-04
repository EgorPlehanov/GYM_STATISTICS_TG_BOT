"""Тесты internal API."""

from fastapi.testclient import TestClient
from pydantic import SecretStr


def test_internal_health_requires_token(monkeypatch):
    """Проверяет, что `/internal/health` закрыт без service token."""
    _set_required_env(monkeypatch)

    from app.api.main import app

    client = TestClient(app)
    response = client.get("/internal/health")

    assert response.status_code == 401


def test_internal_health_rejects_invalid_token(monkeypatch):
    """Проверяет отказ при неверном service token."""
    _set_required_env(monkeypatch)

    from app.api.deps import config
    from app.api.main import app

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    client = TestClient(app)
    response = client.get(
        "/internal/health",
        headers={"X-Internal-Api-Key": "invalid-token"},
    )

    assert response.status_code == 401


def test_internal_health_accepts_valid_token(monkeypatch):
    """Проверяет успешный internal health check с верным service token."""
    _set_required_env(monkeypatch)

    from app.api.deps import config
    from app.api.main import app

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    client = TestClient(app)
    response = client.get(
        "/internal/health",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def _set_required_env(monkeypatch):
    """Заполняет обязательные настройки для импорта FastAPI приложения в тестах."""
    monkeypatch.setenv("MAIN_ADMIN_ID", "1")
    monkeypatch.setenv("TG_BOT_TOKEN", "1:test")
    monkeypatch.setenv("TG_BOT_USERNAME", "test_bot")
    monkeypatch.setenv("POSTGRES_USER", "gym")
    monkeypatch.setenv("POSTGRES_PASSWORD", "gym")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_DB", "gym")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret-with-at-least-32-bytes")
    monkeypatch.setenv("INTERNAL_API_TOKEN", "test-internal-token-with-at-least-32-bytes")
