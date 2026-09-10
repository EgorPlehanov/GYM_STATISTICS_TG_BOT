"""Тесты internal API."""

from datetime import date, datetime
from types import SimpleNamespace

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
        "training_data": {
            "id": 10,
            "user_id": 123456789,
            "date": "2026-09-09",
            "comment": "Тест",
            "global_set_counter": 1,
            "exercises": {},
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
        "training_data": {
            "id": None,
            "user_id": 123456789,
            "date": "2026-09-09",
            "comment": None,
            "global_set_counter": 0,
            "exercises": {},
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

    async def fake_save_training_data(session, training_data):
        """Фиксирует восстановленную FSM-структуру перед сохранением."""
        calls.append({"session": session, "training_data": training_data})
        return 10, False, True

    async def fake_db_session():
        """Возвращает тестовую заглушку DB-сессии."""
        yield object()

    monkeypatch.setattr(
        internal_trainings,
        "save_training_data",
        fake_save_training_data,
    )
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.post(
        "/internal/bot/trainings",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
        json={
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
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "training_id": 10,
        "updated": False,
        "created": True,
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
