"""Клиент backend API для Telegram-бота."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx

from app.core.config import config


@dataclass(frozen=True)
class EnsureUserResult:
    """Результат регистрации пользователя через internal API.

    Attributes:
        created: признак того, что пользователь был создан в текущем запросе.
    """

    created: bool


@dataclass(frozen=True)
class BotExercise:
    """Упражнение, полученное ботом через backend API.

    Attributes:
        id: внутренний id упражнения из справочника.
        name: название упражнения для кнопок и inline-результатов.
        description: описание упражнения для inline-подсказки.
    """

    id: int
    name: str
    description: str | None


@dataclass(frozen=True)
class BotTrainingByDateResult:
    """Данные тренировки за дату, полученные через backend API.

    Attributes:
        exists: признак того, что тренировка уже была в базе.
        training_data: структура тренировки в формате FSM-сценария бота.
    """

    exists: bool
    training_data: dict[str, Any]


@dataclass(frozen=True)
class BotTrainingSaveResult:
    """Результат сохранения тренировки через backend API.

    Attributes:
        training_id: внутренний id сохраненной тренировки.
        updated: признак обновления существующей тренировки.
        created: признак создания новой тренировки.
    """

    training_id: int
    updated: bool
    created: bool


class BotApiClient:
    """HTTP-клиент, через который Telegram-бот обращается к backend API."""

    def __init__(
        self,
        base_url: str | None = None,
        internal_api_token: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Создает клиент backend API для Telegram-бота.

        Args:
            base_url: базовый URL API. По умолчанию берется из `BOT_API_BASE_URL`.
            internal_api_token: service token для `/internal/*`.
            http_client: готовый `httpx.AsyncClient` для тестов или внешнего управления.
        """
        self.base_url = (base_url or config.BOT_API_BASE_URL).rstrip("/")
        self.internal_api_token = (
            internal_api_token or config.INTERNAL_API_TOKEN.get_secret_value()
        )
        self._client = http_client
        self._owns_client = http_client is None

    async def __aenter__(self) -> "BotApiClient":
        """Открывает HTTP-клиент, если он не был передан извне."""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        """Закрывает HTTP-клиент, созданный внутри `BotApiClient`."""
        if self._owns_client and self._client is not None:
            await self._client.aclose()
        self._client = None

    async def ensure_user(
        self,
        telegram_id: int,
        name: str,
        language_code: str | None,
    ) -> EnsureUserResult:
        """Создает пользователя через internal API, если его еще нет.

        Args:
            telegram_id: Telegram user id из update-а бота.
            name: отображаемое имя пользователя.
            language_code: языковой код пользователя из Telegram.

        Returns:
            `EnsureUserResult` с признаком создания пользователя.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.post(
            "/internal/bot/users/ensure",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "telegram_id": telegram_id,
                "name": name,
                "language_code": language_code,
            },
        )
        response.raise_for_status()
        return EnsureUserResult(**response.json())

    async def get_exercises(
        self,
        telegram_id: int,
        page_size: int = 50,
        page_num: int = 0,
        substring: str | None = None,
    ) -> list[BotExercise]:
        """Возвращает упражнения для выбора в Telegram-боте.

        Args:
            telegram_id: Telegram user id для пользовательской сортировки.
            page_size: размер страницы.
            page_num: номер страницы, начиная с 0.
            substring: строка поиска по справочнику упражнений.

        Returns:
            список упражнений в формате, удобном для handlers/keyboards бота.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        params: dict[str, int | str] = {
            "telegram_id": telegram_id,
            "page_size": page_size,
            "page_num": page_num,
        }
        if substring is not None:
            params["substring"] = substring

        response = await self._client.get(
            "/internal/bot/exercises",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params=params,
        )
        response.raise_for_status()
        return [BotExercise(**item) for item in response.json()]

    async def get_exercise(self, exercise_id: int) -> BotExercise:
        """Возвращает одно упражнение по id через internal API.

        Args:
            exercise_id: внутренний id упражнения из справочника.

        Returns:
            упражнение, найденное backend API.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.get(
            f"/internal/bot/exercises/{exercise_id}",
            headers={"X-Internal-Api-Key": self.internal_api_token},
        )
        response.raise_for_status()
        return BotExercise(**response.json())

    async def get_training_dates(self, telegram_id: int) -> list[date]:
        """Возвращает даты тренировок пользователя для календаря бота.

        Args:
            telegram_id: Telegram user id пользователя.

        Returns:
            список дат тренировок, преобразованный из JSON-строк в `date`.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.get(
            "/internal/bot/trainings/dates",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={"telegram_id": telegram_id},
        )
        response.raise_for_status()
        return [date.fromisoformat(item) for item in response.json()]

    async def get_training_by_date(
        self,
        telegram_id: int,
        training_date: datetime,
    ) -> BotTrainingByDateResult:
        """Возвращает тренировку пользователя за дату или пустую структуру.

        Args:
            telegram_id: Telegram user id пользователя.
            training_date: дата, выбранная в Telegram-боте.

        Returns:
            результат с флагом существования и FSM-структурой тренировки.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.get(
            "/internal/bot/trainings/by-date",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={
                "telegram_id": telegram_id,
                "training_date": training_date.isoformat(),
            },
        )
        response.raise_for_status()

        payload = response.json()
        return BotTrainingByDateResult(
            exists=payload["exists"],
            training_data=_deserialize_training_data(payload["training_data"]),
        )

    async def save_training(
        self,
        training_data: dict[str, Any],
    ) -> BotTrainingSaveResult:
        """Сохраняет тренировку через internal API.

        Args:
            training_data: FSM-структура тренировки бота.

        Returns:
            результат сохранения тренировки в backend API.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.post(
            "/internal/bot/trainings",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "training_data": _serialize_training_data(training_data),
            },
        )
        response.raise_for_status()
        return BotTrainingSaveResult(**response.json())

    async def delete_training(self, training_id: int) -> None:
        """Удаляет тренировку через internal API.

        Args:
            training_id: внутренний id тренировки.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.delete(
            f"/internal/bot/trainings/{training_id}",
            headers={"X-Internal-Api-Key": self.internal_api_token},
        )
        response.raise_for_status()

    async def get_redirect_group_ids(self, telegram_id: int) -> list[int]:
        """Возвращает группы, куда нужно отправить результат тренировки.

        Args:
            telegram_id: Telegram user id пользователя.

        Returns:
            список Telegram chat id групп с включенным редиректом результата.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.get(
            "/internal/bot/groups/redirect-targets",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={"telegram_id": telegram_id},
        )
        response.raise_for_status()
        return list(response.json())

    async def get_training_result_message_id(
        self,
        group_id: int,
        training_id: int,
    ) -> int | None:
        """Возвращает Telegram message id результата тренировки в группе.

        Args:
            group_id: Telegram chat id группы.
            training_id: id сохраненной тренировки.

        Returns:
            Telegram message id или `None`, если запись не найдена.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.get(
            f"/internal/bot/groups/{group_id}/training-results/{training_id}/message",
            headers={"X-Internal-Api-Key": self.internal_api_token},
        )
        response.raise_for_status()
        return response.json()["message_id"]

    async def create_training_result_message(
        self,
        group_id: int,
        training_id: int,
        message_id: int,
    ) -> None:
        """Создает запись о сообщении результата тренировки.

        Args:
            group_id: Telegram chat id группы.
            training_id: id сохраненной тренировки.
            message_id: Telegram message id отправленного результата.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.post(
            "/internal/bot/groups/training-result-messages",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "group_id": group_id,
                "training_id": training_id,
                "message_id": message_id,
            },
        )
        response.raise_for_status()

    async def update_training_result_message(
        self,
        group_id: int,
        training_id: int,
        new_message_id: int,
    ) -> bool:
        """Обновляет Telegram message id результата тренировки.

        Args:
            group_id: Telegram chat id группы.
            training_id: id сохраненной тренировки.
            new_message_id: новый Telegram message id после повторной отправки.

        Returns:
            признак того, что существующая запись была найдена и обновлена.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.patch(
            "/internal/bot/groups/training-result-messages",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "group_id": group_id,
                "training_id": training_id,
                "new_message_id": new_message_id,
            },
        )
        response.raise_for_status()
        return response.json()["updated"]

    async def update_group_bot_banned(
        self,
        group_id: int,
        is_bot_banned: bool,
    ) -> None:
        """Обновляет признак недоступности группы для Telegram-бота.

        Args:
            group_id: Telegram chat id группы.
            is_bot_banned: признак того, что бот удален или заблокирован в группе.
        """
        if self._client is None:
            raise RuntimeError("BotApiClient должен использоваться внутри async context manager")

        response = await self._client.patch(
            f"/internal/bot/groups/{group_id}/bot-banned",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={"is_bot_banned": is_bot_banned},
        )
        response.raise_for_status()


def _serialize_training_data(training_data: dict[str, Any]) -> dict[str, Any]:
    """Готовит FSM-структуру тренировки к отправке через JSON.

    Args:
        training_data: структура с `datetime` и числовыми ключами `exercises`/`sets`.

    Returns:
        JSON-совместимый словарь с ISO-датами и строковыми ключами.
    """
    serialized = dict(training_data)
    if isinstance(serialized.get("date"), datetime):
        serialized["date"] = serialized["date"].isoformat()

    exercises = {}
    for exercise_id, exercise_data in serialized.get("exercises", {}).items():
        exercise = dict(exercise_data)
        exercise["sets"] = {
            str(set_id): _serialize_set_data(set_data)
            for set_id, set_data in exercise.get("sets", {}).items()
        }
        exercises[str(exercise_id)] = exercise

    serialized["exercises"] = exercises
    return serialized


def _serialize_set_data(set_data: dict[str, Any]) -> dict[str, Any]:
    """Готовит данные подхода к отправке через JSON."""
    serialized = dict(set_data)
    if isinstance(serialized.get("time"), datetime):
        serialized["time"] = serialized["time"].isoformat()
    return serialized


def _deserialize_training_data(training_data: dict[str, Any]) -> dict[str, Any]:
    """Восстанавливает FSM-структуру тренировки после передачи через JSON.

    Args:
        training_data: JSON-словарь, полученный от internal API.

    Returns:
        структура тренировки с `datetime` и числовыми ключами `exercises`/`sets`.
    """
    restored = dict(training_data)
    if restored.get("date") is not None:
        restored["date"] = datetime.fromisoformat(restored["date"])

    exercises = {}
    for exercise_id, exercise_data in restored.get("exercises", {}).items():
        exercise = dict(exercise_data)
        exercise["sets"] = {
            int(set_id): _deserialize_set_data(set_data)
            for set_id, set_data in exercise.get("sets", {}).items()
        }
        exercises[int(exercise_id)] = exercise

    restored["exercises"] = exercises
    return restored


def _deserialize_set_data(set_data: dict[str, Any]) -> dict[str, Any]:
    """Восстанавливает данные подхода после передачи через JSON."""
    restored = dict(set_data)
    if restored.get("time") is not None:
        restored["time"] = datetime.fromisoformat(restored["time"])
    return restored


