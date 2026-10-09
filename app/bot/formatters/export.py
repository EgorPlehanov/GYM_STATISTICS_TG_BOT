from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import Protocol

from openpyxl import Workbook


class ExportDataRow(Protocol):
    """Минимальные данные строки, необходимые для XLSX-экспорта."""

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


def get_export_data_file(export_data: list[ExportDataRow]) -> bytes:
    """Создает XLSX-файл для отправки пользователю через Telegram."""
    workbook = Workbook()
    sheet = workbook.active

    headers = [
        'Дата',
        'Комментарий',
        'Название упражнения',
        '№ подхода в тренировке',
        '№ подхода в упражнении на тренировке',
        'Вес в подходе',
        'Повторения в подходе',
        'Сумма весов всех подходов упражнения на тренировке',
        'Сумма повторений всех подходов упражнения на тренировке',
        'Количество подходов упражнения на тренировке',
        'Количество подходов на тренировке',
        'Сумма весов всех подходов упражнения всех тренировок',
        'Сумма повторений всех подходов упражнения всех тренировок',
        'Количество подходов упражнения всех тренировок',
        'Максимальное значение веса в упражнении',
        'Название ранга в упражнении',
        'Количество звезд в ранге в упражнении',
        'Звезды в ранге в упражнении',
        'Количество подходов всех тренировок'
    ]
    sheet.append(headers)

    for item in export_data:
        row = [
            item.date,
            item.comment,
            item.exercise_name,
            item.overall_order,
            item.exercise_order,
            item.weight,
            item.repetitions,
            item.training_exercise_weight_sum,
            item.training_exercise_repetitions_sum,
            item.training_exercise_sets_count,
            item.training_sets_count,
            item.exercise_all_weight_sum,
            item.exercise_all_repetitions_sum,
            item.exercise_all_sets_count,
            item.exercise_rank_value,
            item.exercise_rank_name,
            item.exercise_rank_star_count,
            item.exercise_rank_star_level,
            item.all_sets_count
        ]
        sheet.append(row)

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()

