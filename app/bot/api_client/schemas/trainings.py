"""DTO-схемы API-клиента Telegram-бота для тренировок."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from app.bot.api_client.schemas.exercises import BotExercise


@dataclass(frozen=True)
class BotTrainingSet:
    """Подход тренировки из strict DTO internal API.

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


@dataclass(frozen=True)
class BotTrainingExercise:
    """Упражнение тренировки из strict DTO internal API.

    Attributes:
        exercise_id: внутренний id упражнения.
        exercise_name: название упражнения для отображения.
        sets: подходы упражнения в порядке выполнения.
    """

    exercise_id: int
    exercise_name: str
    sets: list[BotTrainingSet]


@dataclass(frozen=True)
class BotTraining:
    """Тренировка из strict DTO internal API.

    Attributes:
        training_id: внутренний id тренировки, если запись уже существует.
        training_date: дата тренировки.
        comment: комментарий к тренировке.
        exercises: упражнения и подходы тренировки.
    """

    training_id: int | None
    training_date: date
    comment: str | None
    exercises: list[BotTrainingExercise]


@dataclass(frozen=True)
class BotTrainingByDateResult:
    """Данные тренировки за дату, полученные через backend API.

    Attributes:
        exists: признак того, что тренировка уже была в базе.
        training: структура тренировки в strict DTO internal API.
    """

    exists: bool
    training: BotTraining


@dataclass(frozen=True)
class BotTrainingSetMode:
    """Подсказка веса и повторений для одного порядкового подхода.

    Attributes:
        weight_mode: наиболее частый вес подхода.
        repetitions_mode: наиболее частое количество повторений.
    """

    weight_mode: float
    repetitions_mode: int


@dataclass(frozen=True)
class BotTrainingExerciseMode:
    """Подсказки подходов для одного упражнения.

    Attributes:
        max_exercise_order: наибольший номер подхода с рассчитанной подсказкой.
        sets_modes: подсказки по номеру подхода.
    """

    max_exercise_order: int
    sets_modes: dict[int, BotTrainingSetMode]


@dataclass(frozen=True)
class BotTrainingStartContext:
    """Стартовые данные для сценария добавления тренировки.

    Attributes:
        most_frequent_exercises: упражнения для первичной клавиатуры выбора.
        weight_repetitions_modes: подсказки веса и повторений по прошлым тренировкам.
        training_dates: даты существующих тренировок для календаря.
    """

    most_frequent_exercises: list[BotExercise]
    weight_repetitions_modes: dict[int, BotTrainingExerciseMode]
    training_dates: list[date]


class BotTrainingSaveOutcome(str, Enum):
    """Семантический результат сохранения тренировки через internal API."""

    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"


@dataclass(frozen=True)
class BotTrainingSaveResult:
    """Результат сохранения тренировки через backend API.

    Attributes:
        training_id: внутренний id сохраненной тренировки.
        outcome: единый семантический результат сохранения.
    """

    training_id: int
    outcome: BotTrainingSaveOutcome
