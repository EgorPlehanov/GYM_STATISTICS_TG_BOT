"""Тесты HTTP-клиента Telegram-бота."""

import json

import httpx
import pytest


@pytest.mark.asyncio
async def test_bot_api_client_ensure_user_sends_internal_token(monkeypatch):
    """Проверяет payload и service token при регистрации пользователя через bot client."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует HTTP-запрос клиента и возвращает успешный ответ API."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        captured_request["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"created": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://api:8000",
    ) as http_client:
        api_client = BotApiClient(
            base_url="http://api:8000",
            internal_api_token="internal-test-token",
            http_client=http_client,
        )
        async with api_client:
            result = await api_client.ensure_user(
                telegram_id=123456789,
                name="Egor",
                language_code="ru",
            )

    assert result.created is True
    assert captured_request == {
        "method": "POST",
        "url": "http://api:8000/internal/bot/users/ensure",
        "token": "internal-test-token",
        "payload": {
            "telegram_id": 123456789,
            "name": "Egor",
            "language_code": "ru",
        },
    }


@pytest.mark.asyncio
async def test_bot_api_client_get_exercises_sends_internal_token(monkeypatch):
    """Проверяет запрос списка упражнений через internal API."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует GET-запрос клиента и возвращает список упражнений."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        return httpx.Response(
            200,
            json=[
                {
                    "id": 1,
                    "name": "Жим лежа",
                    "description": "Упражнение на развитие грудных мышц",
                }
            ],
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://api:8000",
    ) as http_client:
        api_client = BotApiClient(
            base_url="http://api:8000",
            internal_api_token="internal-test-token",
            http_client=http_client,
        )
        async with api_client:
            result = await api_client.get_exercises(
                telegram_id=123456789,
                page_size=50,
                page_num=1,
                substring="жим",
            )

    assert len(result) == 1
    assert result[0].id == 1
    assert result[0].name == "Жим лежа"
    assert captured_request == {
        "method": "GET",
        "url": (
            "http://api:8000/internal/bot/exercises?"
            "telegram_id=123456789&page_size=50&page_num=1&substring=%D0%B6%D0%B8%D0%BC"
        ),
        "token": "internal-test-token",
    }


@pytest.mark.asyncio
async def test_bot_api_client_get_exercise_sends_internal_token(monkeypatch):
    """Проверяет запрос одного упражнения через internal API."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует GET-запрос клиента и возвращает упражнение."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        return httpx.Response(
            200,
            json={
                "id": 1,
                "name": "Жим лежа",
                "description": "Упражнение на развитие грудных мышц",
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://api:8000",
    ) as http_client:
        api_client = BotApiClient(
            base_url="http://api:8000",
            internal_api_token="internal-test-token",
            http_client=http_client,
        )
        async with api_client:
            result = await api_client.get_exercise(exercise_id=1)

    assert result.id == 1
    assert result.name == "Жим лежа"
    assert captured_request == {
        "method": "GET",
        "url": "http://api:8000/internal/bot/exercises/1",
        "token": "internal-test-token",
    }


def _set_required_env(monkeypatch):
    """Заполняет обязательные настройки для импорта bot client в тестах."""
    monkeypatch.setenv("MAIN_ADMIN_ID", "1")
    monkeypatch.setenv("TG_BOT_TOKEN", "1:test")
    monkeypatch.setenv("TG_BOT_USERNAME", "test_bot")
    monkeypatch.setenv("POSTGRES_USER", "gym")
    monkeypatch.setenv("POSTGRES_PASSWORD", "gym")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_DB", "gym")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret-with-at-least-32-bytes")
    monkeypatch.setenv("INTERNAL_API_TOKEN", "test-internal-token-with-at-least-32-bytes")
