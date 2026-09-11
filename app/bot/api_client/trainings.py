"""Методы API-клиента Telegram-бота для тренировок."""

from datetime import date, datetime
from typing import Any

from app.bot.api_client.base import BotApiClientBase
from app.bot.api_client.schemas.exercises import BotExercise
from app.bot.api_client.schemas.trainings import (
    BotTrainingByDateResult,
    BotTrainingSaveResult,
    BotTrainingStartContext,
)


class BotTrainingsApiClientMixin(BotApiClientBase):
    """Методы internal API для работы Telegram-бота с тренировками."""

    async def get_training_dates(self, telegram_id: int) -> list[date]:
        """Возвращает даты тренировок пользователя для календаря бота.

        Args:
            telegram_id: Telegram user id пользователя.

        Returns:
            список дат тренировок, преобразованный из JSON-строк в `date`.
        """
        client = self._get_client()

        response = await client.get(
            "/internal/bot/trainings/dates",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={"telegram_id": telegram_id},
        )
        response.raise_for_status()
        return [date.fromisoformat(item) for item in response.json()]

    async def get_training_start_context(
        self,
        telegram_id: int,
        page_size: int = 15,
        last_training_count: int = 12,
    ) -> BotTrainingStartContext:
        """Возвращает стартовые данные для команды `/training`.

        Args:
            telegram_id: Telegram user id пользователя.
            page_size: количество частых упражнений для первичной клавиатуры.
            last_training_count: количество последних тренировок для расчета подсказок.

        Returns:
            контекст для сохранения в FSM state перед выбором даты.
        """
        client = self._get_client()

        response = await client.get(
            "/internal/bot/trainings/start-context",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            params={
                "telegram_id": telegram_id,
                "page_size": page_size,
                "last_training_count": last_training_count,
            },
        )
        response.raise_for_status()

        payload = response.json()
        return BotTrainingStartContext(
            most_frequent_exercises=[
                BotExercise(**item) for item in payload["most_frequent_exercises"]
            ],
            weight_repetitions_modes=_restore_weight_repetitions_modes(
                payload["weight_repetitions_modes"]
            ),
        )

    async def get_training_by_date(
        self,
        telegram_id: int,
        training_date: date,
    ) -> BotTrainingByDateResult:
        """Возвращает тренировку пользователя за дату или пустую структуру.

        Args:
            telegram_id: Telegram user id пользователя.
            training_date: дата, выбранная в Telegram-боте.

        Returns:
            результат с флагом существования и FSM-структурой тренировки.
        """
        client = self._get_client()

        response = await client.get(
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
        client = self._get_client()

        response = await client.post(
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
        client = self._get_client()

        response = await client.delete(
            f"/internal/bot/trainings/{training_id}",
            headers={"X-Internal-Api-Key": self.internal_api_token},
        )
        response.raise_for_status()


def _serialize_training_data(training_data: dict[str, Any]) -> dict[str, Any]:
    """Готовит FSM-структуру тренировки к отправке через JSON.

    Args:
        training_data: структура с `date`, `datetime` в подходах и числовыми ключами.

    Returns:
        JSON-совместимый словарь с ISO-датой тренировки, ISO-временем подходов и строковыми ключами.
    """
    serialized = dict(training_data)
    if isinstance(serialized.get("date"), datetime):
        serialized["date"] = serialized["date"].date().isoformat()
    elif isinstance(serialized.get("date"), date):
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
        структура тренировки с `date`, `datetime` в подходах и числовыми ключами.
    """
    restored = dict(training_data)
    if restored.get("date") is not None:
        restored["date"] = date.fromisoformat(restored["date"])

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


def _restore_weight_repetitions_modes(
    weight_repetitions_modes: dict[str, Any],
) -> dict[int, dict[str, Any]]:
    """Восстанавливает числовые ключи подсказок после JSON.

    Args:
        weight_repetitions_modes: JSON-словарь подсказок с ключами-строками.

    Returns:
        словарь с `int` ключами упражнений и подходов для старых FSM-утилит.
    """
    restored = {}
    for exercise_id, exercise_mode in weight_repetitions_modes.items():
        restored[int(exercise_id)] = {
            **exercise_mode,
            "sets_modes": {
                int(set_id): set_mode
                for set_id, set_mode in exercise_mode.get("sets_modes", {}).items()
            },
        }
    return restored
