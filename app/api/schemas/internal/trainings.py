"""DTO-схемы internal API для тренировок Telegram-бота."""

from datetime import date, datetime
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


class InternalBotTrainingSet(BaseModel):
    """Подход упражнения в strict DTO internal API.

    Attributes:
        set_id: внутренний id подхода, если подход уже сохранен.
        set_number: порядковый номер подхода в тренировке.
        weight: вес в килограммах.
        repetitions: количество повторений.
        execution_time: время выполнения подхода.
    """

    set_id: int | None
    set_number: int
    weight: float
    repetitions: int
    execution_time: datetime | None = None


class InternalBotTrainingExercise(BaseModel):
    """Упражнение тренировки в strict DTO internal API.

    Attributes:
        exercise_id: внутренний id упражнения.
        exercise_name: название упражнения для отображения.
        sets: подходы упражнения в порядке выполнения.
    """

    exercise_id: int
    exercise_name: str
    sets: list[InternalBotTrainingSet]


class InternalBotTrainingData(BaseModel):
    """Тренировка в strict DTO internal API для Telegram-бота.

    Attributes:
        training_id: внутренний id тренировки, если запись уже существует.
        training_date: дата тренировки.
        comment: комментарий к тренировке.
        exercises: упражнения и подходы тренировки.
    """

    training_id: int | None
    training_date: date
    comment: str | None = None
    exercises: list[InternalBotTrainingExercise]


class InternalBotTrainingByDateResponse(BaseModel):
    """Данные тренировки за дату для сценариев Telegram-бота.

    Attributes:
        exists: признак того, что тренировка уже была в базе.
        training: структура тренировки в строгом internal API-формате.
    """

    exists: bool
    training: InternalBotTrainingData


class InternalBotTrainingSaveRequest(BaseModel):
    """Данные для сохранения тренировки из Telegram-бота.

    Attributes:
        telegram_id: Telegram user id владельца тренировки.
        training: структура тренировки в строгом internal API-формате.
    """

    telegram_id: int
    training: InternalBotTrainingData


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
