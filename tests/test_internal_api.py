"""Тесты internal API."""

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
    from app.api.routers import internal

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
        internal,
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
    from app.api.routers import internal

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
        internal,
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
    from app.api.routers import internal

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

    monkeypatch.setattr(internal, "get_exercise_by_id", fake_get_exercise_by_id)
    app.dependency_overrides[get_db_session] = fake_db_session

    client = TestClient(app)
    response = client.get(
        "/internal/bot/exercises/999",
        headers={"X-Internal-Api-Key": "test-internal-token-with-at-least-32-bytes"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Упражнение не найдено"}


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
