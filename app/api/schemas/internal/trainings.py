"""DTO-схемы internal API для тренировок Telegram-бота."""

from typing import Any

from pydantic import BaseModel

from app.api.schemas.internal.exercises import InternalBotExerciseResponse


class InternalBotTrainingStartContextResponse(BaseModel):
    """Стартовые данные для сценария добавления тренировки в Telegram-боте.

    Attributes:
        most_frequent_exercises: упражнения, отсортированные под пользователя.
        weight_repetitions_modes: подсказки веса и повторений по прошлым тренировкам.
    """

    most_frequent_exercises: list[InternalBotExerciseResponse]
    weight_repetitions_modes: dict[int, Any]


class InternalBotTrainingByDateResponse(BaseModel):
    """Данные тренировки за дату для сценариев Telegram-бота.

    Attributes:
        exists: признак того, что тренировка уже была в базе.
        training_data: структура тренировки в старом FSM-формате бота.
    """

    exists: bool
    training_data: dict[str, Any]


class InternalBotTrainingSaveRequest(BaseModel):
    """Данные для сохранения тренировки из Telegram-бота.

    Attributes:
        training_data: структура тренировки в старом FSM-формате бота после JSON.
    """

    training_data: dict[str, Any]


class InternalBotTrainingSaveResponse(BaseModel):
    """Результат сохранения тренировки из Telegram-бота.

    Attributes:
        training_id: id сохраненной тренировки.
        updated: признак обновления существующей тренировки.
        created: признак создания новой тренировки.
    """

    training_id: int
    updated: bool
    created: bool
