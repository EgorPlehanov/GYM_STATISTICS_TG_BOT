"""Тесты security helpers и API авторизации."""

import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient
from pydantic import SecretStr


def _build_telegram_hash(auth_data: dict[str, object], bot_token: str) -> str:
    """Собирает эталонный hash Telegram Login Widget для тестовых данных."""
    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(auth_data.items())
        if key != "hash" and value is not None
    )
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


def test_telegram_login_hash_validation(monkeypatch):
    """Проверяет валидную и невалидную подпись Telegram Login Widget."""
    _set_required_env(monkeypatch)

    from app.core.security import is_telegram_login_hash_valid

    bot_token = "1:test"
    auth_data = {
        "id": 123456789,
        "first_name": "Egor",
        "last_name": "Test",
        "username": "egor_test",
        "photo_url": None,
        "auth_date": 1_700_000_000,
    }
    auth_data["hash"] = _build_telegram_hash(auth_data, bot_token)

    assert is_telegram_login_hash_valid(auth_data, bot_token)

    auth_data["first_name"] = "Changed"

    assert not is_telegram_login_hash_valid(auth_data, bot_token)


def test_session_token_round_trip(monkeypatch):
    """Проверяет создание и чтение подписанного session token."""
    _set_required_env(monkeypatch)

    from app.core import security

    monkeypatch.setattr(
        security.config,
        "SESSION_SECRET_KEY",
        SecretStr("test-secret-with-at-least-32-bytes"),
    )
    monkeypatch.setattr(security.config, "SESSION_TTL_SECONDS", 3600)

    token = security.create_session_token(user_id=42)
    payload = security.decode_session_token(token)

    assert payload["sub"] == "42"
    assert "telegram_id" not in payload


def test_auth_me_requires_session(monkeypatch):
    """Проверяет, что `/api/auth/me` закрыт без session cookie."""
    _set_required_env(monkeypatch)

    from app.api.main import app

    client = TestClient(app)
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_auth_me_returns_current_user(monkeypatch):
    """Проверяет DTO ответа `/api/auth/me` для авторизованного пользователя."""
    _set_required_env(monkeypatch)

    from app.api.deps import get_current_user
    from app.api.main import app

    user = SimpleNamespace(
        id=7,
        telegram_id=123456789,
        name="Egor",
        language_code="ru",
    )
    app.dependency_overrides[get_current_user] = lambda: user
    client = TestClient(app)

    response = client.get("/api/auth/me")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "id": 7,
        "telegram_id": 123456789,
        "name": "Egor",
        "language_code": "ru",
    }


def test_telegram_login_sets_http_only_cookie(monkeypatch):
    """Проверяет, что login endpoint устанавливает session cookie."""
    _set_required_env(monkeypatch)

    from app.api.deps import get_db_session
    from app.api.main import app
    from app.api.routers import auth as auth_router
    from app.core.config import config

    monkeypatch.setattr(
        auth_router.config,
        "SESSION_SECRET_KEY",
        SecretStr("test-secret-with-at-least-32-bytes"),
    )

    async def fake_authenticate_telegram_login(session, login_data):
        """Возвращает пользователя без обращения к базе данных."""
        return SimpleNamespace(
            id=7,
            telegram_id=login_data.id,
            name=login_data.first_name,
            language_code=None,
        )

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        auth_router,
        "authenticate_telegram_login",
        fake_authenticate_telegram_login,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    auth_date = int((datetime.now(timezone.utc) - timedelta(seconds=5)).timestamp())
    payload = {
        "id": 123456789,
        "first_name": "Egor",
        "last_name": None,
        "username": "egor_test",
        "photo_url": None,
        "auth_date": auth_date,
        "hash": "fake-hash",
    }
    client = TestClient(app)

    response = client.post("/api/auth/telegram-login", json=payload)

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["telegram_id"] == 123456789
    assert config.SESSION_COOKIE_NAME in response.cookies
    assert "httponly" in response.headers["set-cookie"].lower()


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
