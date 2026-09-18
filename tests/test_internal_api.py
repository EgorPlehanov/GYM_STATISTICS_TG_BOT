"""Тесты internal API."""

from datetime import date, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.domain.trainings.schemas import TrainingSaveOutcome


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


def test_internal_bot_user_ensure_requires_token(monkeypatch):
    """Проверяет, что регистрация пользователя бота закрыта без service token."""
    _set_required_env(monkeypatch)

    from app.api.main import app

    client = TestClient(app)
    response = client.post(
        "/internal/bot/users/ensure",
        json={
            "telegram_id": 123456789,
            "name": "Egor",
            "language_code": "ru",
        },
    )

    assert response.status_code == 401


def test_internal_bot_user_ensure_calls_domain_service(monkeypatch):
    """Проверяет, что internal endpoint регистрации пользователя вызывает domain service."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import users as internal_users

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_create_user_if_not_exists(session, user_id, name, language_code):
        """Фиксирует параметры вызова без обращения к базе данных."""
        calls.append(
            {
                "session": session,
                "user_id": user_id,
                "name": name,
                "language_code": language_code,
            }
        )
        return True

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_users,
        "create_user_if_not_exists",
        fake_create_user_if_not_exists,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.post(
        "/internal/bot/users/ensure",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={
            "telegram_id": 123456789,
            "name": "Egor",
            "language_code": "ru",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"created": True}
    assert calls == [
        {
            "session": calls[0]["session"],
            "user_id": 123456789,
            "name": "Egor",
            "language_code": "ru",
        }
    ]


def test_internal_bot_user_private_chat_banned_calls_domain_service(monkeypatch):
    """Проверяет обновление блокировки личного чата через internal API."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import users as internal_users

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_update_user_private_chat_banned(
        session,
        user_id,
        is_private_chat_banned,
    ):
        """Фиксирует параметры обновления блокировки личного чата."""
        calls.append(
            {
                "session": session,
                "user_id": user_id,
                "is_private_chat_banned": is_private_chat_banned,
            }
        )

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_users,
        "update_user_private_chat_banned",
        fake_update_user_private_chat_banned,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.patch(
        "/internal/bot/users/123456789/private-chat-banned",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={"is_private_chat_banned": True},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == [
        {
            "session": calls[0]["session"],
            "user_id": 123456789,
            "is_private_chat_banned": True,
        }
    ]


def test_internal_bot_admin_access_calls_domain_service(monkeypatch):
    """Проверяет получение доступа к Telegram admin-панели через internal API."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import admin as internal_admin

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_get_user_role_codes_by_telegram_id(session, telegram_id):
        """Фиксирует параметры получения ролей пользователя."""
        calls.append({"session": session, "telegram_id": telegram_id})
        return ["owner"]

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_admin,
        "get_user_role_codes_by_telegram_id",
        fake_get_user_role_codes_by_telegram_id,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/admin/access",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        params={"telegram_id": 123456789},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "has_access": True,
        "roles": ["owner"],
    }
    assert calls == [{"session": calls[0]["session"], "telegram_id": 123456789}]


def test_internal_bot_admin_status_calls_domain_service(monkeypatch):
    """Проверяет минимальный статус backend API для Telegram admin-панели."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import admin as internal_admin

    monkeypatch.setattr(config, "APP_ENV", "test")
    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_get_user_role_codes_by_telegram_id(session, telegram_id):
        """Фиксирует параметры получения ролей пользователя."""
        calls.append({"session": session, "telegram_id": telegram_id})
        return ["admin"]

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_admin,
        "get_user_role_codes_by_telegram_id",
        fake_get_user_role_codes_by_telegram_id,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/admin/status",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        params={"telegram_id": 123456789},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "api_status": "ok",
        "app_env": "test",
        "has_access": True,
        "roles": ["admin"],
    }
    assert calls == [{"session": calls[0]["session"], "telegram_id": 123456789}]


def test_internal_bot_exercises_calls_domain_service(monkeypatch):
    """Проверяет, что список упражнений для бота берется через domain service."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import exercises as internal_exercises

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_get_sorted_exercises_by_sets_count(
        session,
        user_id,
        page_size,
        page_num,
        substring,
    ):
        """Фиксирует параметры сортированного списка упражнений."""
        calls.append(
            {
                "session": session,
                "user_id": user_id,
                "page_size": page_size,
                "page_num": page_num,
                "substring": substring,
            }
        )
        return [
            SimpleNamespace(
                id=1,
                name="Жим лежа",
                description="Упражнение на развитие грудных мышц",
            )
        ]

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_exercises,
        "get_sorted_exercises_by_sets_count",
        fake_get_sorted_exercises_by_sets_count,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/exercises",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        params={
            "telegram_id": 123456789,
            "page_size": 50,
            "page_num": 1,
            "substring": "жим",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "Жим лежа",
            "description": "Упражнение на развитие грудных мышц",
        }
    ]
    assert calls == [
        {
            "session": calls[0]["session"],
            "user_id": 123456789,
            "page_size": 50,
            "page_num": 1,
            "substring": "жим",
        }
    ]


def test_internal_bot_exercise_returns_404_when_not_found(monkeypatch):
    """Проверяет понятный ответ, если упражнение для бота не найдено."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import exercises as internal_exercises

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    async def fake_get_exercise_by_id(session, exercise_id):
        """Возвращает пустой результат без обращения к базе данных."""
        return None

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_exercises,
        "get_exercise_by_id",
        fake_get_exercise_by_id,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/exercises/999",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Упражнение не найдено"}


def test_internal_bot_training_dates_calls_domain_service(monkeypatch):
    """Проверяет, что даты тренировок для бота берутся через domain service."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import trainings as internal_trainings

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_get_training_date_by_user_id(session, user_id):
        """Фиксирует параметры запроса дат тренировок."""
        calls.append({"session": session, "user_id": user_id})
        return [date(2026, 9, 1), date(2026, 9, 9)]

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_trainings,
        "get_training_date_by_user_id",
        fake_get_training_date_by_user_id,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/trainings/dates",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        params={"telegram_id": 123456789},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == ["2026-09-01", "2026-09-09"]
    assert calls == [{"session": calls[0]["session"], "user_id": 123456789}]


def test_internal_bot_training_start_context_calls_domain_service(monkeypatch):
    """Проверяет получение стартового контекста тренировки через domain service."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import trainings as internal_trainings

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_get_sorted_exercises_by_sets_count(
        session,
        user_id,
        page_size,
    ):
        """Фиксирует параметры получения частых упражнений."""
        calls.append(("exercises", session, user_id, page_size))
        return [
            SimpleNamespace(
                id=1,
                name="Жим лежа",
                description="Упражнение на развитие грудных мышц",
            )
        ]

    async def fake_get_exercises_weight_repetitions_modes(
        session,
        user_id,
        last_training_count,
    ):
        """Фиксирует параметры получения подсказок веса и повторений."""
        calls.append(("modes", session, user_id, last_training_count))
        return {
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

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_trainings,
        "get_sorted_exercises_by_sets_count",
        fake_get_sorted_exercises_by_sets_count,
    )
    monkeypatch.setattr(
        internal_trainings,
        "get_exercises_weight_repetitions_modes",
        fake_get_exercises_weight_repetitions_modes,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/trainings/start-context",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        params={
            "telegram_id": 123456789,
            "page_size": 15,
            "last_training_count": 12,
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
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
    }
    assert calls == [
        ("exercises", calls[0][1], 123456789, 15),
        ("modes", calls[0][1], 123456789, 12),
    ]


def test_internal_bot_training_by_date_returns_existing_training(monkeypatch):
    """Проверяет получение существующей тренировки для Telegram-бота."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import trainings as internal_trainings

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_check_training_exists_for_user_and_date(session, user_id, date):
        """Фиксирует проверку существования тренировки."""
        calls.append(("exists", session, user_id, date))
        return True

    async def fake_get_training_data_by_date_and_user(session, user_id, date):
        """Возвращает старый FSM-формат тренировки без обращения к базе."""
        calls.append(("get", session, user_id, date))
        return {
            "id": 10,
            "user_id": user_id,
            "date": date,
            "comment": "Тест",
            "global_set_counter": 1,
            "exercises": {},
        }

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_trainings,
        "check_training_exists_for_user_and_date",
        fake_check_training_exists_for_user_and_date,
    )
    monkeypatch.setattr(
        internal_trainings,
        "get_training_data_by_date_and_user",
        fake_get_training_data_by_date_and_user,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/trainings/by-date",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        params={
            "telegram_id": 123456789,
            "training_date": "2026-09-09",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "exists": True,
        "training": {
            "training_id": 10,
            "training_date": "2026-09-09",
            "comment": "Тест",
            "exercises": [],
        },
    }
    assert calls == [
        ("exists", calls[0][1], 123456789, date(2026, 9, 9)),
        ("get", calls[0][1], 123456789, date(2026, 9, 9)),
    ]


def test_internal_bot_training_by_date_returns_empty_training(monkeypatch):
    """Проверяет пустую структуру, если тренировки за дату еще нет."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import trainings as internal_trainings

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    async def fake_check_training_exists_for_user_and_date(session, user_id, date):
        """Возвращает признак отсутствия тренировки без обращения к базе."""
        return False

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_trainings,
        "check_training_exists_for_user_and_date",
        fake_check_training_exists_for_user_and_date,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/trainings/by-date",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        params={
            "telegram_id": 123456789,
            "training_date": "2026-09-09",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "exists": False,
        "training": {
            "training_id": None,
            "training_date": "2026-09-09",
            "comment": None,
            "exercises": [],
        },
    }


def test_internal_bot_training_save_calls_domain_service(monkeypatch):
    """Проверяет сохранение тренировки из Telegram-бота через domain service."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import trainings as internal_trainings

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_save_training(session, training_data):
        """Фиксирует восстановленную FSM-структуру перед сохранением."""
        calls.append({"session": session, "training_data": training_data})
        return 10, TrainingSaveOutcome.CREATED

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_trainings,
        "save_training",
        fake_save_training,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.post(
        "/internal/bot/trainings",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={
            "telegram_id": 123456789,
            "training": {
                "training_id": None,
                "training_date": "2026-09-09",
                "comment": None,
                "exercises": [
                    {
                        "exercise_id": 1,
                        "exercise_name": "Жим лежа",
                        "sets": [
                            {
                                "set_id": None,
                                "set_number": 1,
                                "weight": 100.0,
                                "repetitions": 5,
                                "execution_time": "2026-09-09T12:35:00",
                            }
                        ],
                    }
                ],
            }
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "training_id": 10,
        "outcome": "created",
    }
    assert calls == [
        {
            "session": calls[0]["session"],
            "training_data": {
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
            },
        }
    ]


def test_internal_bot_training_delete_calls_domain_service(monkeypatch):
    """Проверяет удаление тренировки из Telegram-бота через domain service."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import trainings as internal_trainings

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_delete_training_by_id(session, training_id):
        """Фиксирует параметры удаления тренировки."""
        calls.append({"session": session, "training_id": training_id})

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_trainings,
        "delete_training_by_id",
        fake_delete_training_by_id,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.delete(
        "/internal/bot/trainings/10",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == [{"session": calls[0]["session"], "training_id": 10}]


def test_internal_bot_redirect_targets_calls_domain_service(monkeypatch):
    """Проверяет получение групп для редиректа результата тренировки."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_get_user_group_to_redirect(session, user_id):
        """Фиксирует параметры получения групп редиректа."""
        calls.append({"session": session, "user_id": user_id})
        return [-1001, -1002]

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_groups,
        "get_user_group_to_redirect",
        fake_get_user_group_to_redirect,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/groups/redirect-targets",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        params={"telegram_id": 123456789},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [-1001, -1002]
    assert calls == [{"session": calls[0]["session"], "user_id": 123456789}]


def test_internal_bot_group_ensure_calls_domain_service(monkeypatch):
    """Проверяет создание или восстановление группы через internal API."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_create_group_if_not_exists(session, id, group_type, name):
        """Фиксирует параметры создания или восстановления группы."""
        calls.append(
            {
                "session": session,
                "id": id,
                "group_type": group_type,
                "name": name,
            }
        )
        return True

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_groups,
        "create_group_if_not_exists",
        fake_create_group_if_not_exists,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.post(
        "/internal/bot/groups/ensure",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={
            "group_id": -1001,
            "group_name": "Спортзал",
            "group_type": "supergroup",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"created": True}
    assert calls == [
        {
            "session": calls[0]["session"],
            "id": -1001,
            "group_type": "supergroup",
            "name": "Спортзал",
        }
    ]


def test_internal_bot_group_admin_calls_domain_service(monkeypatch):
    """Проверяет обновление признака администратора бота через internal API."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_update_group_is_bot_admin(session, group_id, is_bot_admin):
        """Фиксирует параметры обновления признака администратора бота."""
        calls.append(
            {
                "session": session,
                "group_id": group_id,
                "is_bot_admin": is_bot_admin,
            }
        )

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_groups,
        "update_group_is_bot_admin",
        fake_update_group_is_bot_admin,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.patch(
        "/internal/bot/groups/-1001/bot-admin",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={"is_bot_admin": True},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == [
        {
            "session": calls[0]["session"],
            "group_id": -1001,
            "is_bot_admin": True,
        }
    ]


def test_internal_bot_group_migrate_to_supergroup_calls_domain_service(monkeypatch):
    """Проверяет миграцию группы в супергруппу через internal API."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_update_group_to_supergroup(
        session,
        group_id,
        supergroup_id,
        supergroup_name,
        supergroup_type,
    ):
        """Фиксирует параметры миграции группы в супергруппу."""
        calls.append(
            {
                "session": session,
                "group_id": group_id,
                "supergroup_id": supergroup_id,
                "supergroup_name": supergroup_name,
                "supergroup_type": supergroup_type,
            }
        )

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_groups,
        "update_group_to_supergroup",
        fake_update_group_to_supergroup,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.patch(
        "/internal/bot/groups/migrate-to-supergroup",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={
            "group_id": -1001,
            "supergroup_id": -1002,
            "supergroup_name": "Новый спортзал",
            "supergroup_type": "supergroup",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == [
        {
            "session": calls[0]["session"],
            "group_id": -1001,
            "supergroup_id": -1002,
            "supergroup_name": "Новый спортзал",
            "supergroup_type": "supergroup",
        }
    ]


def test_internal_bot_group_user_delete_calls_domain_service(monkeypatch):
    """Проверяет удаление связи пользователя с группой через internal API."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_delete_group_user(session, group_id, user_id):
        """Фиксирует параметры удаления связи пользователя с группой."""
        calls.append(
            {
                "session": session,
                "group_id": group_id,
                "user_id": user_id,
            }
        )

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(internal_groups, "delete_group_user", fake_delete_group_user)
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.delete(
        "/internal/bot/groups/-1001/users/123456789",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == [
        {
            "session": calls[0]["session"],
            "group_id": -1001,
            "user_id": 123456789,
        }
    ]


def test_internal_bot_group_user_admin_calls_domain_service(monkeypatch):
    """Проверяет обновление статуса администратора пользователя через internal API."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_update_group_user_is_admin(session, group_id, user_id, is_admin):
        """Фиксирует параметры обновления статуса администратора."""
        calls.append(
            {
                "session": session,
                "group_id": group_id,
                "user_id": user_id,
                "is_admin": is_admin,
            }
        )

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_groups,
        "update_group_user_is_admin",
        fake_update_group_user_is_admin,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.patch(
        "/internal/bot/groups/-1001/users/123456789/admin",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={"is_admin": True},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == [
        {
            "session": calls[0]["session"],
            "group_id": -1001,
            "user_id": 123456789,
            "is_admin": True,
        }
    ]


def test_internal_bot_redirect_settings_calls_domain_service(monkeypatch):
    """Проверяет получение групп пользователя для настройки редиректа."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_get_all_user_redirect_groups(session, user_id):
        """Фиксирует параметры получения настроек редиректа."""
        calls.append({"session": session, "user_id": user_id})
        return [
            SimpleNamespace(
                id=7,
                group_id=-1001,
                group_name="Спортзал",
                is_redirect_to_group=True,
            )
        ]

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_groups,
        "get_all_user_redirect_groups",
        fake_get_all_user_redirect_groups,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/groups/redirect-settings",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        params={"telegram_id": 123456789},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 7,
            "group_id": -1001,
            "group_name": "Спортзал",
            "is_redirect_to_group": True,
        }
    ]
    assert calls == [{"session": calls[0]["session"], "user_id": 123456789}]


def test_internal_bot_current_group_redirect_toggle_creates_link(monkeypatch):
    """Проверяет включение редиректа при первой настройке группы."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_create_group_if_not_exists(session, id, group_type, name):
        """Фиксирует создание группы перед настройкой редиректа."""
        calls.append(("create_group", session, id, group_type, name))
        return True

    async def fake_get_group_user_by_user_id_and_group_id(session, user_id, group_id):
        """Возвращает отсутствие связи пользователя с группой."""
        calls.append(("get_group_user", session, user_id, group_id))
        return None

    async def fake_create_group_user(
        session,
        user_id,
        group_id,
        is_user_admin,
        is_redirect_to_group,
    ):
        """Фиксирует создание связи пользователя с группой."""
        calls.append(
            (
                "create_group_user",
                session,
                user_id,
                group_id,
                is_user_admin,
                is_redirect_to_group,
            )
        )
        return True

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_groups,
        "create_group_if_not_exists",
        fake_create_group_if_not_exists,
    )
    monkeypatch.setattr(
        internal_groups,
        "get_group_user_by_user_id_and_group_id",
        fake_get_group_user_by_user_id_and_group_id,
    )
    monkeypatch.setattr(internal_groups, "create_group_user", fake_create_group_user)
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.post(
        "/internal/bot/groups/redirect-settings/toggle-current",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={
            "telegram_id": 123456789,
            "group_id": -1001,
            "group_name": "Спортзал",
            "group_type": "supergroup",
            "is_user_admin": True,
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "is_redirect_to_group": True,
        "created": True,
    }
    assert [call[:1] + call[2:] for call in calls] == [
        ("create_group", -1001, "SUPERGROUP", "Спортзал"),
        ("get_group_user", 123456789, -1001),
        ("create_group_user", 123456789, -1001, True, True),
    ]


def test_internal_bot_current_group_redirect_toggle_updates_existing_link(monkeypatch):
    """Проверяет переключение редиректа для существующей связи с группой."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_create_group_if_not_exists(session, id, group_type, name):
        """Фиксирует проверку группы перед настройкой редиректа."""
        calls.append(("create_group", session, id, group_type, name))
        return False

    async def fake_get_group_user_by_user_id_and_group_id(session, user_id, group_id):
        """Возвращает существующую связь пользователя с группой."""
        calls.append(("get_group_user", session, user_id, group_id))
        return SimpleNamespace(is_redirect_to_group=True)

    async def fake_update_redirect_to_group(
        session,
        group_id,
        user_id,
        is_redirect_to_group,
    ):
        """Фиксирует обновление состояния редиректа."""
        calls.append(("update_redirect", session, group_id, user_id, is_redirect_to_group))

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_groups,
        "create_group_if_not_exists",
        fake_create_group_if_not_exists,
    )
    monkeypatch.setattr(
        internal_groups,
        "get_group_user_by_user_id_and_group_id",
        fake_get_group_user_by_user_id_and_group_id,
    )
    monkeypatch.setattr(
        internal_groups,
        "update_redirect_to_group",
        fake_update_redirect_to_group,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.post(
        "/internal/bot/groups/redirect-settings/toggle-current",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={
            "telegram_id": 123456789,
            "group_id": -1001,
            "group_name": "Спортзал",
            "group_type": "supergroup",
            "is_user_admin": True,
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "is_redirect_to_group": False,
        "created": False,
    }
    assert [call[:1] + call[2:] for call in calls] == [
        ("create_group", -1001, "SUPERGROUP", "Спортзал"),
        ("get_group_user", 123456789, -1001),
        ("update_redirect", -1001, 123456789, False),
    ]


def test_internal_bot_redirect_setting_update_calls_domain_service(monkeypatch):
    """Проверяет обновление настройки редиректа из inline-меню."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_update_redirect_to_group(
        session,
        group_id,
        user_id,
        is_redirect_to_group,
    ):
        """Фиксирует обновление состояния редиректа."""
        calls.append(
            {
                "session": session,
                "group_id": group_id,
                "user_id": user_id,
                "is_redirect_to_group": is_redirect_to_group,
            }
        )

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_groups,
        "update_redirect_to_group",
        fake_update_redirect_to_group,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.patch(
        "/internal/bot/groups/redirect-settings",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={
            "telegram_id": 123456789,
            "group_id": -1001,
            "is_redirect_to_group": False,
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == [
        {
            "session": calls[0]["session"],
            "group_id": -1001,
            "user_id": 123456789,
            "is_redirect_to_group": False,
        }
    ]


def test_internal_bot_training_result_message_calls_domain_service(monkeypatch):
    """Проверяет операции с Telegram message id результата тренировки."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_get_group_training_result_messages_id(session, group_id, training_id):
        """Фиксирует параметры получения Telegram message id."""
        calls.append(("get", session, group_id, training_id))
        return 42

    async def fake_create_group_training_result_message(
        session,
        group_id,
        training_id,
        message_id,
    ):
        """Фиксирует параметры создания записи о Telegram message id."""
        calls.append(("create", session, group_id, training_id, message_id))

    async def fake_update_group_training_result_message_id(
        session,
        group_id,
        training_id,
        new_message_id,
    ):
        """Фиксирует параметры обновления Telegram message id."""
        calls.append(("update", session, group_id, training_id, new_message_id))
        return True

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_groups,
        "get_group_training_result_messages_id",
        fake_get_group_training_result_messages_id,
    )
    monkeypatch.setattr(
        internal_groups,
        "create_group_training_result_message",
        fake_create_group_training_result_message,
    )
    monkeypatch.setattr(
        internal_groups,
        "update_group_training_result_message_id",
        fake_update_group_training_result_message_id,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    headers = {"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"}
    get_response = client.get(
        "/internal/bot/groups/-1001/training-results/10/message",
        headers=headers,
    )
    create_response = client.post(
        "/internal/bot/groups/training-result-messages",
        headers=headers,
        json={
            "group_id": -1001,
            "training_id": 10,
            "message_id": 42,
        },
    )
    update_response = client.patch(
        "/internal/bot/groups/training-result-messages",
        headers=headers,
        json={
            "group_id": -1001,
            "training_id": 10,
            "new_message_id": 43,
        },
    )

    app.dependency_overrides.clear()

    assert get_response.status_code == 200
    assert get_response.json() == {"message_id": 42}
    assert create_response.status_code == 200
    assert create_response.json() == {"status": "ok"}
    assert update_response.status_code == 200
    assert update_response.json() == {"updated": True}
    assert [call[:1] + call[2:] for call in calls] == [
        ("get", -1001, 10),
        ("create", -1001, 10, 42),
        ("update", -1001, 10, 43),
    ]


def test_internal_bot_group_banned_calls_domain_service(monkeypatch):
    """Проверяет обновление признака недоступности группы для Telegram-бота."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import groups as internal_groups

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_update_group_is_bot_banned(session, group_id, is_bot_banned):
        """Фиксирует параметры обновления группы."""
        calls.append(
            {
                "session": session,
                "group_id": group_id,
                "is_bot_banned": is_bot_banned,
            }
        )

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_groups,
        "update_group_is_bot_banned",
        fake_update_group_is_bot_banned,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.patch(
        "/internal/bot/groups/-1001/bot-banned",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={"is_bot_banned": True},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == [
        {
            "session": calls[0]["session"],
            "group_id": -1001,
            "is_bot_banned": True,
        }
    ]


def test_internal_bot_user_rating_recalculate_calls_domain_service(monkeypatch):
    """Проверяет запуск пересчета рейтинга пользователя через internal API."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import ratings as internal_ratings

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_update_or_create_user_exercise_rating(session, user_id):
        """Фиксирует параметры пересчета рейтинга."""
        calls.append({"session": session, "user_id": user_id})

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_ratings,
        "update_or_create_user_exercise_rating",
        fake_update_or_create_user_exercise_rating,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.post(
        "/internal/bot/users/123456789/rating/recalculate",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert calls == [{"session": calls[0]["session"], "user_id": 123456789}]


def test_internal_bot_statistics_exercise_rating_calls_domain_service(monkeypatch):
    """Проверяет получение статистики пользователя через internal API."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import statistics as internal_statistics

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_get_user_exercise_rating(session, user_id):
        """Фиксирует параметры получения статистики пользователя."""
        calls.append({"session": session, "user_id": user_id})
        return [
            SimpleNamespace(
                exercise_id=1,
                exercise_name="Жим лежа",
                rank_name="Новичок",
                rank_level=2,
                rating_value=100.0,
            )
        ]

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_statistics,
        "get_user_exercise_rating",
        fake_get_user_exercise_rating,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/statistics/exercise-rating",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        params={"telegram_id": 123456789},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "exercise_id": 1,
            "exercise_name": "Жим лежа",
            "rank_name": "Новичок",
            "rank_level": 2,
            "rating_value": 100.0,
        }
    ]
    assert calls == [{"session": calls[0]["session"], "user_id": 123456789}]


def test_internal_bot_export_data_calls_domain_service(monkeypatch):
    """Проверяет получение данных экспорта через internal API."""
    _set_required_env(monkeypatch)

    from app.api.deps import config, get_db_session
    from app.api.main import app
    from app.api.routers.internal import export as internal_export

    monkeypatch.setattr(
        config,
        "INTERNAL_API_TOKEN",
        SecretStr("test-internal-token-with-at-least-32-bytes"),
    )

    calls = []

    async def fake_get_export_data(session, user_id):
        """Фиксирует параметры получения данных экспорта."""
        calls.append({"session": session, "user_id": user_id})
        return [
            SimpleNamespace(
                date=date(2026, 9, 9),
                comment="Тест",
                exercise_name="Жим лежа",
                overall_order=1,
                exercise_order=1,
                weight=100.0,
                repetitions=5,
                training_exercise_weight_sum=500.0,
                training_exercise_repetitions_sum=5,
                training_exercise_sets_count=1,
                training_sets_count=1,
                exercise_all_weight_sum=500.0,
                exercise_all_repetitions_sum=5,
                exercise_all_sets_count=1,
                exercise_rank_value=100.0,
                exercise_rank_name="Новичок",
                exercise_rank_star_count=2,
                exercise_rank_star_level="⭐⭐",
                all_sets_count=1,
            )
        ]

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(internal_export, "get_export_data", fake_get_export_data)
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/export/data",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        params={"telegram_id": 123456789},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
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
    ]
    assert calls == [{"session": calls[0]["session"], "user_id": 123456789}]


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
