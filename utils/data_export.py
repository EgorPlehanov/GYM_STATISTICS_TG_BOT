from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession
from db.queries import get_export_data


async def get_export_data_file(
    session: AsyncSession,
    user_id: int
):
    """
    Создает эксель файл для экспорта данных
    """
    export_data = await get_export_data(session, user_id)
    # print(export_data)
    workbook = Workbook()
    sheet = workbook.active

    # Write headers
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

    # Write data
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

    # Save the workbook to a buffer
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()