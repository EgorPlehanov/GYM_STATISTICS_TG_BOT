"""Тесты HTTP-клиента Telegram-бота."""

import json
from datetime import date, datetime

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
async def test_bot_api_client_update_user_private_chat_banned_sends_internal_token(
    monkeypatch,
):
    """Проверяет обновление блокировки личного чата через internal API."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует PATCH-запрос обновления блокировки личного чата."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        captured_request["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"status": "ok"})

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
            await api_client.update_user_private_chat_banned(
                telegram_id=123456789,
                is_private_chat_banned=True,
            )

    assert captured_request == {
        "method": "PATCH",
        "url": "http://api:8000/internal/bot/users/123456789/private-chat-banned",
        "token": "internal-test-token",
        "payload": {"is_private_chat_banned": True},
    }


@pytest.mark.asyncio
async def test_bot_api_client_admin_methods_send_internal_token(monkeypatch):
    """Проверяет методы клиента для минимальной Telegram admin-панели."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        """Возвращает ответы для проверки доступа и статуса admin-панели."""
        captured_requests.append(
            {
                "method": request.method,
                "url": str(request.url),
                "token": request.headers.get("X-Internal-Api-Key"),
            }
        )
        if request.url.path.endswith("/access"):
            return httpx.Response(
                200,
                json={
                    "has_access": True,
                    "roles": ["owner"],
                },
            )
        return httpx.Response(
            200,
            json={
                "api_status": "ok",
                "app_env": "test",
                "has_access": True,
                "roles": ["owner"],
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
            access = await api_client.get_admin_access(telegram_id=123456789)
            status = await api_client.get_admin_status(telegram_id=123456789)

    assert access.has_access is True
    assert access.roles == ["owner"]
    assert status.api_status == "ok"
    assert status.app_env == "test"
    assert status.roles == ["owner"]
    assert captured_requests == [
        {
            "method": "GET",
            "url": "http://api:8000/internal/bot/admin/access?telegram_id=123456789",
            "token": "internal-test-token",
        },
        {
            "method": "GET",
            "url": "http://api:8000/internal/bot/admin/status?telegram_id=123456789",
            "token": "internal-test-token",
        },
    ]


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


@pytest.mark.asyncio
async def test_bot_api_client_get_training_dates_sends_internal_token(monkeypatch):
    """Проверяет запрос дат тренировок через internal API."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует GET-запрос клиента и возвращает даты тренировок."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        return httpx.Response(200, json=["2026-09-01", "2026-09-09"])

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
            result = await api_client.get_training_dates(telegram_id=123456789)

    assert result == [date(2026, 9, 1), date(2026, 9, 9)]
    assert captured_request == {
        "method": "GET",
        "url": "http://api:8000/internal/bot/trainings/dates?telegram_id=123456789",
        "token": "internal-test-token",
    }


@pytest.mark.asyncio
async def test_bot_api_client_get_training_start_context_restores_modes(monkeypatch):
    """Проверяет получение стартового контекста `/training` через internal API."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует GET-запрос и возвращает JSON с ключами-строками."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        return httpx.Response(
            200,
            json={
                "most_frequent_exercises": [
                    {
                        "id": 1,
                        "name": "Жим лежа",
                        "description": "Упражнение на развитие грудных мышц",
                    }
                ],
                "weight_repetitions_modes": {
                    "1": {
                        "max_exercise_order": 1,
                        "sets_modes": {
                            "1": {
                                "weight_mode": 100.0,
                                "repetitions_mode": 5,
                            }
                        },
                    }
                },
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
            result = await api_client.get_training_start_context(
                telegram_id=123456789,
                page_size=15,
                last_training_count=12,
            )

    assert result.most_frequent_exercises[0].id == 1
    assert result.most_frequent_exercises[0].name == "Жим лежа"
    assert result.weight_repetitions_modes == {
        1: {
            "max_exercise_order": 1,
            "sets_modes": {
                1: {
                    "weight_mode": 100.0,
                    "repetitions_mode": 5,
                }
            },
        }
    }
    assert captured_request == {
        "method": "GET",
        "url": (
            "http://api:8000/internal/bot/trainings/start-context?"
            "telegram_id=123456789&page_size=15&last_training_count=12"
        ),
        "token": "internal-test-token",
    }


@pytest.mark.asyncio
async def test_bot_api_client_get_training_by_date_restores_fsm_data(monkeypatch):
    """Проверяет восстановление FSM-структуры тренировки после JSON."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Возвращает тренировку с JSON-ключами, которые должны стать `int`."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        return httpx.Response(
            200,
            json={
                "exists": True,
                "training_data": {
                    "id": 10,
                    "user_id": 123456789,
                    "date": "2026-09-09",
                    "comment": "Тест",
                    "global_set_counter": 1,
                    "exercises": {
                        "1": {
                            "exercise_name": "Жим лежа",
                            "local_set_counter": 1,
                            "sets": {
                                "1": {
                                    "id": 20,
                                    "set_number": 1,
                                    "weight": 100.0,
                                    "repetitions": 5,
                                    "time": "2026-09-09T12:35:00",
                                }
                            },
                        }
                    },
                },
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
            result = await api_client.get_training_by_date(
                telegram_id=123456789,
                training_date=date(2026, 9, 9),
            )

    assert result.exists is True
    assert result.training_data["date"] == date(2026, 9, 9)
    assert list(result.training_data["exercises"].keys()) == [1]
    assert list(result.training_data["exercises"][1]["sets"].keys()) == [1]
    assert result.training_data["exercises"][1]["sets"][1]["time"] == datetime(
        2026,
        9,
        9,
        12,
        35,
    )
    assert captured_request == {
        "method": "GET",
        "url": (
            "http://api:8000/internal/bot/trainings/by-date?"
            "telegram_id=123456789&training_date=2026-09-09"
        ),
        "token": "internal-test-token",
    }


@pytest.mark.asyncio
async def test_bot_api_client_save_training_serializes_fsm_data(monkeypatch):
    """Проверяет сохранение тренировки с JSON-совместимой FSM-структурой."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует POST-запрос клиента и возвращает результат сохранения."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        captured_request["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "training_id": 10,
                "updated": False,
                "created": True,
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
            result = await api_client.save_training(
                {
                    "id": None,
                    "user_id": 123456789,
                    "date": date(2026, 9, 9),
                    "comment": None,
                    "global_set_counter": 1,
                    "exercises": {
                        1: {
                            "exercise_name": "Жим лежа",
                            "local_set_counter": 1,
                            "sets": {
                                1: {
                                    "id": None,
                                    "set_number": 1,
                                    "weight": 100.0,
                                    "repetitions": 5,
                                    "time": datetime(2026, 9, 9, 12, 35),
                                }
                            },
                        }
                    },
                }
            )

    assert result.training_id == 10
    assert result.updated is False
    assert result.created is True
    assert captured_request == {
        "method": "POST",
        "url": "http://api:8000/internal/bot/trainings",
        "token": "internal-test-token",
        "payload": {
            "training_data": {
                "id": None,
                "user_id": 123456789,
                "date": "2026-09-09",
                "comment": None,
                "global_set_counter": 1,
                "exercises": {
                    "1": {
                        "exercise_name": "Жим лежа",
                        "local_set_counter": 1,
                        "sets": {
                            "1": {
                                "id": None,
                                "set_number": 1,
                                "weight": 100.0,
                                "repetitions": 5,
                                "time": "2026-09-09T12:35:00",
                            }
                        },
                    }
                },
            }
        },
    }


@pytest.mark.asyncio
async def test_bot_api_client_delete_training_sends_internal_token(monkeypatch):
    """Проверяет удаление тренировки через internal API."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует DELETE-запрос клиента."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        return httpx.Response(200, json={"status": "ok"})

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
            await api_client.delete_training(training_id=10)

    assert captured_request == {
        "method": "DELETE",
        "url": "http://api:8000/internal/bot/trainings/10",
        "token": "internal-test-token",
    }


@pytest.mark.asyncio
async def test_bot_api_client_redirect_methods_send_internal_token(monkeypatch):
    """Проверяет методы клиента для редиректа результата тренировки."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        """Возвращает ответы для всех redirect-related запросов клиента."""
        payload = json.loads(request.content) if request.content else None
        captured_requests.append(
            {
                "method": request.method,
                "url": str(request.url),
                "token": request.headers.get("X-Internal-Api-Key"),
                "payload": payload,
            }
        )

        if request.url.path.endswith("/redirect-targets"):
            return httpx.Response(200, json=[-1001, -1002])
        if request.method == "GET":
            return httpx.Response(200, json={"message_id": 42})
        if request.method == "PATCH" and request.url.path.endswith("/bot-banned"):
            return httpx.Response(200, json={"status": "ok"})
        if request.method == "PATCH":
            return httpx.Response(200, json={"updated": True})
        return httpx.Response(200, json={"status": "ok"})

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
            redirect_group_ids = await api_client.get_redirect_group_ids(
                telegram_id=123456789,
            )
            message_id = await api_client.get_training_result_message_id(
                group_id=-1001,
                training_id=10,
            )
            await api_client.create_training_result_message(
                group_id=-1001,
                training_id=10,
                message_id=42,
            )
            updated = await api_client.update_training_result_message(
                group_id=-1001,
                training_id=10,
                new_message_id=43,
            )
            await api_client.update_group_bot_banned(
                group_id=-1001,
                is_bot_banned=True,
            )

    assert redirect_group_ids == [-1001, -1002]
    assert message_id == 42
    assert updated is True
    assert captured_requests == [
        {
            "method": "GET",
            "url": "http://api:8000/internal/bot/groups/redirect-targets?telegram_id=123456789",
            "token": "internal-test-token",
            "payload": None,
        },
        {
            "method": "GET",
            "url": "http://api:8000/internal/bot/groups/-1001/training-results/10/message",
            "token": "internal-test-token",
            "payload": None,
        },
        {
            "method": "POST",
            "url": "http://api:8000/internal/bot/groups/training-result-messages",
            "token": "internal-test-token",
            "payload": {
                "group_id": -1001,
                "training_id": 10,
                "message_id": 42,
            },
        },
        {
            "method": "PATCH",
            "url": "http://api:8000/internal/bot/groups/training-result-messages",
            "token": "internal-test-token",
            "payload": {
                "group_id": -1001,
                "training_id": 10,
                "new_message_id": 43,
            },
        },
        {
            "method": "PATCH",
            "url": "http://api:8000/internal/bot/groups/-1001/bot-banned",
            "token": "internal-test-token",
            "payload": {"is_bot_banned": True},
        },
    ]


@pytest.mark.asyncio
async def test_bot_api_client_redirect_settings_methods_send_internal_token(monkeypatch):
    """Проверяет методы клиента для настройки редиректа пользователем."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        """Возвращает ответы для запросов настройки редиректа."""
        payload = json.loads(request.content) if request.content else None
        captured_requests.append(
            {
                "method": request.method,
                "url": str(request.url),
                "token": request.headers.get("X-Internal-Api-Key"),
                "payload": payload,
            }
        )

        if request.method == "GET":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 7,
                        "group_id": -1001,
                        "group_name": "Спортзал",
                        "is_redirect_to_group": True,
                    }
                ],
            )
        if request.method == "POST":
            return httpx.Response(
                200,
                json={
                    "is_redirect_to_group": True,
                    "created": True,
                },
            )
        return httpx.Response(200, json={"status": "ok"})

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
            redirect_groups = await api_client.get_redirect_groups(
                telegram_id=123456789,
            )
            toggle_result = await api_client.toggle_current_group_redirect(
                telegram_id=123456789,
                group_id=-1001,
                group_name="Спортзал",
                group_type="supergroup",
                is_user_admin=True,
            )
            await api_client.update_redirect_group(
                telegram_id=123456789,
                group_id=-1001,
                is_redirect_to_group=False,
            )

    assert redirect_groups[0].group_id == -1001
    assert redirect_groups[0].group_name == "Спортзал"
    assert redirect_groups[0].is_redirect_to_group is True
    assert toggle_result.is_redirect_to_group is True
    assert toggle_result.created is True
    assert captured_requests == [
        {
            "method": "GET",
            "url": "http://api:8000/internal/bot/groups/redirect-settings?telegram_id=123456789",
            "token": "internal-test-token",
            "payload": None,
        },
        {
            "method": "POST",
            "url": "http://api:8000/internal/bot/groups/redirect-settings/toggle-current",
            "token": "internal-test-token",
            "payload": {
                "telegram_id": 123456789,
                "group_id": -1001,
                "group_name": "Спортзал",
                "group_type": "supergroup",
                "is_user_admin": True,
            },
        },
        {
            "method": "PATCH",
            "url": "http://api:8000/internal/bot/groups/redirect-settings",
            "token": "internal-test-token",
            "payload": {
                "telegram_id": 123456789,
                "group_id": -1001,
                "is_redirect_to_group": False,
            },
        },
    ]


@pytest.mark.asyncio
async def test_bot_api_client_group_lifecycle_methods_send_internal_token(monkeypatch):
    """Проверяет методы клиента для событий состояния Telegram-бота в группе."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        """Возвращает ответы для lifecycle-запросов группы."""
        payload = json.loads(request.content) if request.content else None
        captured_requests.append(
            {
                "method": request.method,
                "url": str(request.url),
                "token": request.headers.get("X-Internal-Api-Key"),
                "payload": payload,
            }
        )

        if request.url.path.endswith("/ensure"):
            return httpx.Response(200, json={"created": True})
        return httpx.Response(200, json={"status": "ok"})

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
            is_created = await api_client.ensure_group(
                group_id=-1001,
                group_name="Спортзал",
                group_type="supergroup",
            )
            await api_client.update_group_bot_admin(
                group_id=-1001,
                is_bot_admin=True,
            )
            await api_client.migrate_group_to_supergroup(
                group_id=-1001,
                supergroup_id=-1002,
                supergroup_name="Новый спортзал",
                supergroup_type="supergroup",
            )

    assert is_created is True
    assert captured_requests == [
        {
            "method": "POST",
            "url": "http://api:8000/internal/bot/groups/ensure",
            "token": "internal-test-token",
            "payload": {
                "group_id": -1001,
                "group_name": "Спортзал",
                "group_type": "supergroup",
            },
        },
        {
            "method": "PATCH",
            "url": "http://api:8000/internal/bot/groups/-1001/bot-admin",
            "token": "internal-test-token",
            "payload": {"is_bot_admin": True},
        },
        {
            "method": "PATCH",
            "url": "http://api:8000/internal/bot/groups/migrate-to-supergroup",
            "token": "internal-test-token",
            "payload": {
                "group_id": -1001,
                "supergroup_id": -1002,
                "supergroup_name": "Новый спортзал",
                "supergroup_type": "supergroup",
            },
        },
    ]


@pytest.mark.asyncio
async def test_bot_api_client_group_user_methods_send_internal_token(monkeypatch):
    """Проверяет методы клиента для событий участников Telegram-группы."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует запросы к endpoints участников группы."""
        payload = json.loads(request.content) if request.content else None
        captured_requests.append(
            {
                "method": request.method,
                "url": str(request.url),
                "token": request.headers.get("X-Internal-Api-Key"),
                "payload": payload,
            }
        )
        return httpx.Response(200, json={"status": "ok"})

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
            await api_client.delete_group_user(
                group_id=-1001,
                telegram_id=123456789,
            )
            await api_client.update_group_user_admin(
                group_id=-1001,
                telegram_id=123456789,
                is_admin=True,
            )

    assert captured_requests == [
        {
            "method": "DELETE",
            "url": "http://api:8000/internal/bot/groups/-1001/users/123456789",
            "token": "internal-test-token",
            "payload": None,
        },
        {
            "method": "PATCH",
            "url": "http://api:8000/internal/bot/groups/-1001/users/123456789/admin",
            "token": "internal-test-token",
            "payload": {"is_admin": True},
        },
    ]


@pytest.mark.asyncio
async def test_bot_api_client_recalculate_user_rating_sends_internal_token(monkeypatch):
    """Проверяет запуск пересчета рейтинга через internal API."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует POST-запрос пересчета рейтинга."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        return httpx.Response(200, json={"status": "ok"})

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
            await api_client.recalculate_user_rating(telegram_id=123456789)

    assert captured_request == {
        "method": "POST",
        "url": "http://api:8000/internal/bot/users/123456789/rating/recalculate",
        "token": "internal-test-token",
    }


@pytest.mark.asyncio
async def test_bot_api_client_get_user_exercise_rating_sends_internal_token(monkeypatch):
    """Проверяет получение статистики пользователя через internal API."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует GET-запрос рейтинга упражнений."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        return httpx.Response(
            200,
            json=[
                {
                    "exercise_id": 1,
                    "exercise_name": "Жим лежа",
                    "rank_name": "Новичок",
                    "rank_level": 2,
                    "rating_value": 100.0,
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
            result = await api_client.get_user_exercise_rating(telegram_id=123456789)

    assert len(result) == 1
    assert result[0].exercise_id == 1
    assert result[0].exercise_name == "Жим лежа"
    assert result[0].rank_name == "Новичок"
    assert result[0].rank_level == 2
    assert result[0].rating_value == 100.0
    assert captured_request == {
        "method": "GET",
        "url": ("http://api:8000/internal/bot/statistics/exercise-rating?telegram_id=123456789"),
        "token": "internal-test-token",
    }


@pytest.mark.asyncio
async def test_bot_api_client_get_export_data_restores_date(monkeypatch):
    """Проверяет получение данных экспорта через internal API."""
    _set_required_env(monkeypatch)

    from app.bot.client import BotApiClient

    captured_request = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        """Фиксирует GET-запрос экспорта и возвращает строку данных."""
        captured_request["method"] = request.method
        captured_request["url"] = str(request.url)
        captured_request["token"] = request.headers.get("X-Internal-Api-Key")
        return httpx.Response(
            200,
            json=[
                {
                    "date": "2026-09-09",
                    "comment": "Тест",
                    "exercise_name": "Жим лежа",
                    "overall_order": 1,
                    "exercise_order": 1,
                    "weight": 100.0,
                    "repetitions": 5,
                    "training_exercise_weight_sum": 500.0,
                    "training_exercise_repetitions_sum": 5,
                    "training_exercise_sets_count": 1,
                    "training_sets_count": 1,
                    "exercise_all_weight_sum": 500.0,
                    "exercise_all_repetitions_sum": 5,
                    "exercise_all_sets_count": 1,
                    "exercise_rank_value": 100.0,
                    "exercise_rank_name": "Новичок",
                    "exercise_rank_star_count": 2,
                    "exercise_rank_star_level": "⭐⭐",
                    "all_sets_count": 1,
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
            result = await api_client.get_export_data(telegram_id=123456789)

    assert len(result) == 1
    assert result[0].date == date(2026, 9, 9)
    assert result[0].exercise_name == "Жим лежа"
    assert result[0].weight == 100.0
    assert captured_request == {
        "method": "GET",
        "url": "http://api:8000/internal/bot/export/data?telegram_id=123456789",
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
