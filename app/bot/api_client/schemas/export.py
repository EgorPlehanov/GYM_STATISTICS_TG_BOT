"""DTO-схемы API-клиента Telegram-бота для экспорта."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from app.core.weights import normalize_weight


@dataclass(frozen=True)
class BotExportData:
    """Строка данных для XLSX-экспорта, полученная через backend API.

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
    weight: Decimal
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


def deserialize_export_data(export_data: dict[str, Any]) -> BotExportData:
    """Восстанавливает строку экспорта после JSON.

    Args:
        export_data: JSON-словарь строки экспорта.

    Returns:
        строка экспорта с датой в типе `date`.
    """
    restored = dict(export_data)
    restored["date"] = date.fromisoformat(restored["date"])
    restored["weight"] = normalize_weight(restored["weight"])
    return BotExportData(**restored)
