"""DTO-схемы API-клиента Telegram-бота для тренировок."""

from dataclasses import dataclass
from typing import Any

from app.bot.api_client.schemas.exercises import BotExercise


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
class BotTrainingStartContext:
    """Стартовые данные для сценария добавления тренировки.

    Attributes:
        most_frequent_exercises: упражнения для первичной клавиатуры выбора.
        weight_repetitions_modes: подсказки веса и повторений по прошлым тренировкам.
    """

    most_frequent_exercises: list[BotExercise]
    weight_repetitions_modes: dict[int, dict[str, Any]]


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
