from aiogram.fsm.context import FSMContext
from aiogram import html

from typing import Dict, Union



def format_exercise_data(exercise_data: Dict[str, Union[int, Dict]]):
    """
    Форматирует данные о тренировке
    (упражнения, подходы, вес, количество повторений и время выполнения)
    """
    text_parts = []
    for exercise_id, exercise in exercise_data['exercises'].items():
        text_parts.append(f"◼️ {exercise['exercise_name']}:")

        for set_number, set_data in exercise['sets'].items():
            weight_str = '___.__' if set_data['weight'] is None else f"{set_data['weight']:.2f}"
            repetitions_str = '___' if set_data['repetitions'] is None else f"{set_data['repetitions']}" 
            time_str = '__:__' if set_data['time'] is None else set_data['time'].strftime('%H:%M')
            text_parts.append(f"▫️ {time_str} - {set_data['set_number']}) {weight_str} x {repetitions_str}")

    return "\n".join(text_parts)



def result_format_exercise_data(exercise_data: Dict[str, Union[int, Dict]]):
    """
    Форматирует данные о тренировке
    (упражнения, подходы, вес, количество повторений и время выполнения)
    """
    text_parts = []
    for exercise_id, exercise in exercise_data['exercises'].items():
        text_parts.append(f"◼️ {exercise['exercise_name']}:")

        sets = []
        factor = 0
        cur_weight = ""
        cur_repetitions = ""
        for set_number, set_data in exercise['sets'].items():
            factor += 1
            weight = f"{set_data['weight']}"
            repetitions = f"{set_data['repetitions']}"
            if cur_weight != weight or cur_repetitions != repetitions:
                sets.append(f"{weight}x{repetitions}" + (f"x{factor}" if factor > 1 else ""))
                factor = 0
                cur_weight = weight
                cur_repetitions = repetitions
        
        text_parts.append("▫️ " + ", ".join(sets))

    return "\n".join(text_parts)



def get_training_values(user_data: Dict[str, Union[int, Dict]], is_result: bool = False) -> str:
    """
    Возвращает текст тренировочных значений
    """
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    training_values = []
    if user_data.get('date'):
        date_formatted = user_data['date'].strftime('%d.%m.%Y')
        weekday_name = weekdays[user_data['date'].weekday()]
        comment = ""
        if user_data.get('comment'):
            comment = f" ({html.italic(user_data['comment'])})"
        training_values.append(f"{html.bold(weekday_name)} {html.bold(date_formatted)}{comment}")

        if is_result:
            training_values.append(result_format_exercise_data(user_data['exercise_data']))
        else:
            if user_data.get('exercise_data') and user_data.get('exercise_data').get('exercises'):
                training_values.append(f"Тренировка:\n{format_exercise_data(user_data['exercise_data'])}")
            else:
                training_values.append("Тренировка:\n❗Добавьте упражнения❗")

    if len(training_values) > 0:
        return "\n".join(training_values)
    return None



def get_current_values(user_data: Dict[str, Union[int, Dict]]) -> str:
    """
    Возвращает текст текущих значений
    """
    cur_values = []
    if user_data.get('cur_exercise_name') is not None:
        cur_values.append(f"🏋️‍♂️ Упражнение: {html.bold(html.underline(user_data['cur_exercise_name']))}")
    elif user_data.get('exercise_name') is not None:
        cur_values.append(f"🏋️‍♂️ Упражнение: {html.bold(html.underline(user_data['exercise_name']))}")

    if user_data.get('weight') is not None:
        cur_values.append(f"⚖️ Вес: {html.bold(html.underline(user_data['weight']))} кг")
        
    if user_data.get('repetitions') is not None:
        cur_values.append(f"🔂 Повторения: {html.bold(html.underline(user_data['repetitions']))}")
    
    if len(cur_values) > 0: 
        return "Текущие значения:\n" + "\n".join(cur_values)
    return None



def get_state_text(state: str) -> str:
    """
    Возвращает текст состояния
    """
    state_to_text = {
        "TrainingStates:select_date":           "Выберите дату",
        "TrainingStates:select_exercise":       "Выберите упражнение",
        "TrainingStates:select_weight":         "Выберите доп. вес",
        "TrainingStates:select_repetitions":    "Выберите кол-во повторений",
        "TrainingStates:acept_addition":        "Подтвердите добавление",
        "TrainingStates:menu":                  "Что дальше",
        "TrainingStates:add_comment":           "Отправить комментарий или просто заверши",
        "TrainingStates:edit_choose_exercise":  "Выберите упражнение",
        "TrainingStates:edit_choose_set":       "Выберите подход",
        "TrainingStates:edit_choose_mode":      "Выберите режим",
    }
    return f"⬇️ {state_to_text[state]} ⬇️"



async def get_formatted_state_date(state: FSMContext, is_result: bool = False) -> str:
    """
    Возвращает текст состояния
    """
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    text_list = []

    # text_list.append(f"{user_data['exercise_data']}") # TEST

    training_values = get_training_values(user_data, is_result)
    if training_values is not None:
        text_list.append(training_values)

    if not is_result:
        cur_values = get_current_values(user_data)
        if cur_values is not None:
            text_list.append(cur_values)

        current_state = await state.get_state()
        text_list.append(get_state_text(current_state))
    
    return "\n\n".join(text_list)