from aiogram.fsm.context import FSMContext
from aiogram import html

from typing import Dict, Union
from datetime import datetime
import json

from .formate_set_data_text import format_set_data_to_text
from handlers.training_units import TrainingStates, TrainingMode



def format_exercises_data(
    exercise_data: Dict[str, Union[int, Dict]],
    edit_exercise_id: str = None,
    edit_set_id: int = None,
    delete_acept_flag: bool = False,
) -> str:
    """
    Форматирует данные о тренировке
    (упражнения, подходы, вес, количество повторений и время выполнения)
    """
    delete_all_acept_flag = (
        delete_acept_flag
        and edit_exercise_id is None
        and edit_set_id is None
    )

    text_parts = []
    for exercise_id, exercise in exercise_data['exercises'].items():
        exercise_edit_flag = '✏️ ' if edit_exercise_id == exercise_id or delete_all_acept_flag else ''

        exercise_name = html.bold(exercise['exercise_name'])
        if ((
                delete_acept_flag
                and edit_exercise_id == exercise_id
                and (edit_set_id is None or len(exercise['sets']) == 1)
            ) or delete_all_acept_flag
        ):
            exercise_name = html.strikethrough(exercise_name)
        exercise_text_parts = [f"{exercise_edit_flag}◼️ {exercise_name}:"]

        for set_number, set_data in exercise['sets'].items():

            set_edit_flag = ''
            if (
                edit_exercise_id == exercise_id
                and (edit_set_id is None or edit_set_id == set_number)
                or delete_all_acept_flag
            ):
                set_edit_flag = '✏️ '
            set_text = f"{set_number}) {format_set_data_to_text(set_data, set_id=set_number, is_add_set_number=False)}"

            if delete_acept_flag and set_edit_flag or delete_all_acept_flag:
                set_text = html.strikethrough(set_text)

            exercise_text_parts.append(f"{set_edit_flag}\t▫️ {set_text}")
        
        # text_parts.append("\n".join(exercise_text_parts))
        text_parts.append(html.blockquote("\n".join(exercise_text_parts)))

    return "\n".join(text_parts)



def result_format_exercise_sets(sets_data: Dict[str, Union[int, float, str, datetime]]):
    """
    Форматирует данные подходов 1 упражнения
    """
    format_set = lambda w, r, f: f"{w}×{r}{f'×{f}' if f > 1 else ''}"

    sets = []
    factor = 0
    cur_weight = None
    cur_repetitions = None

    for set_number, set_data in sets_data.items():
        weight = str(set_data['weight']).rstrip('0').rstrip(".")
        repetitions = set_data['repetitions']

        if cur_weight is None and cur_repetitions is None:
            cur_weight = weight
            cur_repetitions = repetitions

        if cur_weight != weight or cur_repetitions != repetitions:
            sets.append(format_set(cur_weight, cur_repetitions, factor))
            factor = 0
            cur_weight = weight
            cur_repetitions = repetitions

        factor += 1
    else:
        sets.append(format_set(cur_weight, cur_repetitions, factor))
    
    return ", ".join(sets)



def result_format_exercise_data(exercise_data: Dict[str, Union[int, Dict]]):
    """
    Форматирует данные о тренировке
    (упражнения, подходы, вес, количество повторений и время выполнения)
    """
    text_parts = []
    for exercise_id, exercise in exercise_data['exercises'].items():
        exercise_text = html.blockquote((
            f"◼️ {exercise['exercise_name']}:\n"
            "\t▫️ " + result_format_exercise_sets(exercise['sets'])
        ))
        text_parts.append(exercise_text)
        # text_parts.append(f"◼️ {exercise['exercise_name']}:")
        # text_parts.append("\t▫️ " + result_format_exercise_sets(exercise['sets']))

    return "\n".join(text_parts)



def get_training_values(
    user_data: Dict[str, Union[int, Dict]],
    is_result: bool = False,
) -> str:
    """
    Возвращает текст тренировочных значений
    """
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    training_values = []

    exercise_data = user_data.get('exercise_data')

    if exercise_data is not None and exercise_data.get('date'):
        date_edit_flag = '✏️ ' if user_data.get('mode') == TrainingMode.EDIT_DATE else ''

        date_formatted = exercise_data['date'].strftime('%d.%m.%Y')
        weekday_name = weekdays[exercise_data['date'].weekday()]
        comment = ""
        if exercise_data.get('comment'):
            # comment = f" ({html.italic(exercise_data['comment'])})"
            comment = html.blockquote(html.italic(exercise_data['comment']))

        training_values.append(f"{date_edit_flag}{html.bold(weekday_name)} {html.bold(date_formatted)}{comment}")

        if is_result:
            training_values.append(f"{html.bold('Тренировка:')}\n{result_format_exercise_data(exercise_data)}")
        else:
            if exercise_data.get('exercises'):
                edit_exercise_id = user_data.get('edit_exercise_id')
                edit_set_id = user_data.get('edit_set_id')

                format_exercise_text = format_exercises_data(
                    exercise_data = exercise_data,
                    edit_exercise_id = edit_exercise_id,
                    edit_set_id = edit_set_id,
                    delete_acept_flag = user_data.get('delete_acept_flag'),
                )

                # training_values.append(f"{html.bold('Тренировка:')}\n{html.blockquote(format_exercise_text)}")
                training_values.append(f"{html.bold('Тренировка:')}\n{format_exercise_text}")
            else:
                training_values.append(f"{html.bold('Тренировка:')}\n{html.blockquote('❗Добавьте упражнения❗')}")

    if len(training_values) > 0:
        return "\n".join(training_values)
    return None



def get_current_values(user_data: Dict[str, Union[int, Dict]]) -> str:
    """
    Возвращает текст текущих значений
    """
    cur_values = []
    if user_data.get('sets_count') is not None and user_data['sets_count'] > 1:
        cur_values.append(f"🔁 Кол-во подходов: x{html.bold(html.underline(user_data['sets_count']))}")

    if user_data.get('edit_exercise_name') is not None:
        cur_values.append(f"🏋️‍♂️ Упражнение: {html.bold(html.underline(user_data['edit_exercise_name']))}")
    elif user_data.get('cur_exercise_name') is not None:
        cur_values.append(f"🏋️‍♂️ Упражнение: {html.bold(html.underline(user_data['cur_exercise_name']))}")
    elif user_data.get('exercise_name') is not None:
        cur_values.append(f"🏋️‍♂️ Упражнение: {html.bold(html.underline(user_data['exercise_name']))}")

    if user_data.get('edit_set_number') is not None:
        cur_values.append(f"🔢 Подход: {html.bold(html.underline(user_data['edit_set_number']))}")

    if user_data.get('weight') is not None:
        cur_values.append(f"⚖️ Вес: {html.bold(html.underline(user_data['weight']))} кг")
        
    if user_data.get('repetitions') is not None:
        cur_values.append(f"🔂 Повторения: {html.bold(html.underline(user_data['repetitions']))}")
    
    if len(cur_values) > 0: 
        return "Текущие значения:\n" + html.blockquote("\n".join(cur_values))
    return None



async def get_delete_object_text(state: FSMContext) -> str:
    """
    Возвращает текст удаляемого объекта
    """
    user_data = await state.get_data()
    edit_exercise_id = user_data.get('edit_exercise_id')
    edit_exercise_name = user_data.get('edit_exercise_name')
    edit_set_id = user_data.get('edit_set_id')
    
    if edit_exercise_id is None:
        return "Всех упражнений с подходами"
    elif edit_set_id is None:
        return f"Всех подходов упражнения {html.underline(edit_exercise_name)}"
    else:
        return f"Подхода упражнения {html.underline(edit_exercise_name)}"



async def get_formatted_other_date(state: FSMContext) -> str:
    """
    Возвращает текст других тренировок
    """
    user_data = await state.get_data()
    canged_exercise_data = user_data.get('changed_exercise_data')
    return f"\n{get_training_values({'exercise_data': canged_exercise_data}, is_result=True)}\n"
    




async def get_state_text(state: FSMContext) -> str:
    """
    Возвращает текст состояния
    """
    state_to_text = {
        TrainingStates.select_date:             "Выберите дату",
        TrainingStates.change_date_acept:       "Что делать с этой тренировкой",
        TrainingStates.select_exercise:         "Выберите упражнение",
        TrainingStates.select_weight:           "Выберите доп. вес",
        TrainingStates.select_repetitions:      "Выберите кол-во повторений",
        TrainingStates.acept_addition:          "Подтвердите добавление",
        TrainingStates.select_sets_count:       "Выберите кол-во добавляемых подходов",
        TrainingStates.menu:                    "Что дальше",
        TrainingStates.add_comment:             "Отправить комментарий или просто заверши",
        TrainingStates.edit_menu:               "Что исправить",
        TrainingStates.edit_select_exercise:    "Выберите упражнение",
        TrainingStates.edit_select_set:         "Выберите подход",
        TrainingStates.edit_delete:             "Подтвердите удаление",
    }
    state_to_adition_text = {
        TrainingStates.edit_delete: await get_delete_object_text(state),
        TrainingStates.change_date_acept: await get_formatted_other_date(state),
    }
    cur_state = await state.get_state()

    adition_text = state_to_adition_text.get(cur_state, '')
    if adition_text != '':
        adition_text = html.blockquote(f"\n❗❗❗ {html.bold(adition_text)} ❗❗❗")

    return f"⬇️ {state_to_text[cur_state]} ⬇️" + adition_text



def serialize_datetime(obj):
    """
    Сериализация даты
    """
    if isinstance(obj, datetime):
        return obj.isoformat()



async def get_formatted_state_date(state: FSMContext, is_result: bool = False) -> str:
    """
    Возвращает текст состояния
    """
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    text_list = []

    # print(json.dumps(user_data.get('exercise_data', {}), default=serialize_datetime, indent=4))

    training_values = get_training_values(user_data, is_result)
    if training_values is not None:
        text_list.append(training_values)

    if not is_result:
        cur_values = get_current_values(user_data)
        if cur_values is not None:
            text_list.append(cur_values)

        text_list.append(await get_state_text(state))
    
    return "\n".join(text_list)