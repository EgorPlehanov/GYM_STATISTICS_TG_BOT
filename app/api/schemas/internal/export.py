"""DTO-схемы internal API для экспорта данных Telegram-бота."""

from datetime import date

from pydantic import BaseModel, ConfigDict


class InternalBotExportDataResponse(BaseModel):
    """Строка данных для XLSX-экспорта в Telegram-боте.

    Attributes:
        date: дата тренировки.
        comment: комментарий к тренировке.
        exercise_name: название упражнения.
        overall_order: номер подхода в тренировке.
        exercise_order: номер подхода в упражнении на тренировке.
        weight: вес в подходе.
        repetitions: количество повторений в подходе.
        training_exercise_weight_sum: сумма весов упражнения в тренировке.
        training_exercise_repetitions_sum: сумма повторений упражнения в тренировке.
        training_exercise_sets_count: количество подходов упражнения в тренировке.
        training_sets_count: количество подходов в тренировке.
        exercise_all_weight_sum: сумма весов упражнения за все тренировки.
        exercise_all_repetitions_sum: сумма повторений упражнения за все тренировки.
        exercise_all_sets_count: количество подходов упражнения за все тренировки.
        exercise_rank_value: максимальное значение веса в рейтинге упражнения.
        exercise_rank_name: название ранга упражнения.
        exercise_rank_star_count: количество звезд ранга упражнения.
        exercise_rank_star_level: строка звезд ранга упражнения.
        all_sets_count: количество всех подходов в выгрузке.
    """

    date: date
    comment: str | None
    exercise_name: str
    overall_order: int
    exercise_order: int
    weight: float
    repetitions: int
    training_exercise_weight_sum: float
    training_exercise_repetitions_sum: int
    training_exercise_sets_count: int
    training_sets_count: int
    exercise_all_weight_sum: float
    exercise_all_repetitions_sum: int
    exercise_all_sets_count: int
    exercise_rank_value: float | None
    exercise_rank_name: str | None
    exercise_rank_star_count: int | None
    exercise_rank_star_level: str | None
    all_sets_count: int

    model_config = ConfigDict(from_attributes=True)
