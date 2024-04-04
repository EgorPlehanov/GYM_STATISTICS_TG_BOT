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
            text_parts.append(f"▫️ {set_data['set_number']}: {weight_str} x {repetitions_str} - {time_str}")

    return "\n".join(text_parts)



async def get_formatted_state_date(state: FSMContext):
    """
    Возвращает текст состояния
    """
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    text_list = []

    # text_list.append(f"{user_data['exercise_data']}") # TEST

    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    # Добавить форматированный текст на основе user_data
    training_values = []
    if user_data.get('date'):
        date_formatted = user_data['date'].strftime('%d.%m.%Y')
        weekday_name = weekdays[user_data['date'].weekday()]
        training_values.append(f"Тренировка {html.bold(weekday_name)} {html.bold(date_formatted)}:")

        if user_data.get('exercise_data') and user_data.get('exercise_data').get('exercises'):
            training_values.append(format_exercise_data(user_data['exercise_data']))
        else:
            training_values.append("❗Добавьте упражнения❗")

    if len(training_values) > 0:
        text_list.append("\n".join(training_values))

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
        text_list.append("Текущие значения:\n" + "\n".join(cur_values))

    # Добавить текст на основе текущего состояния
    state_to_text = {
        "TrainingStates:select_date":           "Выберите дату",
        "TrainingStates:select_exercise":       "Выберите упражнение",
        "TrainingStates:select_weight":         "Выберите доп. вес",
        "TrainingStates:select_repetitions":    "Выберите кол-во повторений",
        "TrainingStates:acept_addition":        "Подтвердите добавление",
        "TrainingStates:menu":                  "Что дальше",
        "TrainingStates:edit_choose_exercise":  "Выберите упражнение",
        "TrainingStates:edit_choose_set":       "Выберите подход",
        "TrainingStates:edit_choose_mode":      "Выберите режим",
    }
    current_state = await state.get_state()
    text_list.append(f"⬇️ {state_to_text[current_state]} ⬇️")
    
    return "\n\n".join(text_list)