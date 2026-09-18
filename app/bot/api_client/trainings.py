"""Методы API-клиента Telegram-бота для тренировок."""

from datetime import date, datetime
from typing import Any

from app.bot.api_client.base import BotApiClientBase
from app.bot.api_client.schemas.exercises import BotExercise
from app.bot.api_client.schemas.trainings import (
    BotTraining,
    BotTrainingByDateResult,
    BotTrainingExercise,
    BotTrainingExerciseMode,
    BotTrainingSaveOutcome,
    BotTrainingSaveResult,
    BotTrainingSet,
    BotTrainingSetMode,
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
            training=_deserialize_training(payload["training"]),
        )

    async def save_training(
        self,
        telegram_id: int,
        training: BotTraining,
    ) -> BotTrainingSaveResult:
        """Сохраняет тренировку через internal API.

        Args:
            telegram_id: Telegram user id владельца тренировки.
            training: strict DTO тренировки.

        Returns:
            результат сохранения тренировки в backend API.
        """
        client = self._get_client()

        response = await client.post(
            "/internal/bot/trainings",
            headers={"X-Internal-Api-Key": self.internal_api_token},
            json={
                "telegram_id": telegram_id,
                "training": _serialize_training(training),
            },
        )
        response.raise_for_status()
        payload = response.json()
        return BotTrainingSaveResult(
            training_id=payload["training_id"],
            outcome=BotTrainingSaveOutcome(payload["outcome"]),
        )

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


def _serialize_training(training: BotTraining) -> dict[str, Any]:
    """Готовит strict DTO тренировки к отправке через JSON.

    Args:
        training: strict DTO тренировки.

    Returns:
        JSON-совместимый словарь для internal API.
    """
    return {
        "training_id": training.training_id,
        "training_date": training.training_date.isoformat(),
        "comment": training.comment,
        "exercises": [
            {
                "exercise_id": exercise.exercise_id,
                "exercise_name": exercise.exercise_name,
                "sets": [_serialize_training_set(set_data) for set_data in exercise.sets],
            }
            for exercise in training.exercises
        ],
    }


def _serialize_training_set(set_data: BotTrainingSet) -> dict[str, Any]:
    """Готовит strict DTO подхода к отправке через JSON."""
    return {
        "set_id": set_data.set_id,
        "set_number": set_data.set_number,
        "weight": set_data.weight,
        "repetitions": set_data.repetitions,
        "execution_time": (
            set_data.execution_time.isoformat()
            if set_data.execution_time is not None
            else None
        ),
    }


def _deserialize_training(training_data: dict[str, Any]) -> BotTraining:
    """Восстанавливает strict DTO тренировки из JSON.

    Args:
        training_data: JSON-словарь, полученный от internal API.

    Returns:
        типизированная структура тренировки.
    """
    return BotTraining(
        training_id=training_data["training_id"],
        training_date=date.fromisoformat(training_data["training_date"]),
        comment=training_data.get("comment"),
        exercises=[
            BotTrainingExercise(
                exercise_id=exercise["exercise_id"],
                exercise_name=exercise["exercise_name"],
                sets=[
                    BotTrainingSet(
                        set_id=set_data.get("set_id"),
                        set_number=set_data["set_number"],
                        weight=set_data["weight"],
                        repetitions=set_data["repetitions"],
                        execution_time=_parse_datetime_or_none(
                            set_data.get("execution_time")
                        ),
                    )
                    for set_data in exercise.get("sets", [])
                ],
            )
            for exercise in training_data.get("exercises", [])
        ],
    )


def _parse_datetime_or_none(value: str | None) -> datetime | None:
    """Возвращает datetime из ISO-строки или None."""
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _restore_weight_repetitions_modes(
    weight_repetitions_modes: dict[str, Any],
) -> dict[int, BotTrainingExerciseMode]:
    """Восстанавливает числовые ключи подсказок после JSON.

    Args:
        weight_repetitions_modes: JSON-словарь подсказок с ключами-строками.

    Returns:
        типизированные подсказки с `int` ключами упражнений и подходов.
    """
    return {
        int(exercise_id): BotTrainingExerciseMode(
            max_exercise_order=exercise_mode["max_exercise_order"],
            sets_modes={
                int(set_id): BotTrainingSetMode(
                    weight_mode=set_mode["weight_mode"],
                    repetitions_mode=set_mode["repetitions_mode"],
                )
                for set_id, set_mode in exercise_mode.get("sets_modes", {}).items()
            },
        )
        for exercise_id, exercise_mode in weight_repetitions_modes.items()
    }
