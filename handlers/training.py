from aiogram import Router, F, html

from aiogram.types import (
    Message, CallbackQuery, InlineQuery,
    InlineQueryResultArticle, InputTextMessageContent,
)

from aiogram.filters import Command, StateFilter
from aiogram.filters.callback_data import CallbackData

from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from contextlib import suppress
from typing import Dict, Union, List, Callable
from datetime import datetime

from keyboards import (
    ikb_select_date,
    DialogCalendar, dialog_cal_callback,
    get_ikb_select_exercise_fab, TrainingExercisePagination, PaginationAction,
    get_ikb_open_inline_search,
    ikb_finish_training,
    get_ikb_edit_select_exercise_fab, EditTrainingExercisePagination,
    ikb_edit_menu_mode,
)


# БД ==================================================================

import random
async def get_most_frequent_exercises() -> List[Dict[str, Union[str, int]]]:
    """
    Returns a random list of exercise names and IDs as a placeholder.
    """
    # Generate a random list of exercise names and IDs
    exercises = [
        {1: 'Приседания'},
        {2: 'Отжимания'},
        {3: 'Планка'},
        {4: 'Выпады'},
        {5: 'Кранчи'},
        {6: 'Отжимания на брусьях'},
        {7: 'Подтягивания'},
        {8: 'Пресс'},
        {9: 'Приседания с гантелями'},
        {10: 'Французский жим'},
        {11: 'Жим ногами'},
        {12: 'Разгибание ног'},
        {13: 'Тяга верхнего блока'},
        # {14: 'Становая тяга'},
        # {15: 'Махи ногой'}
    ]
    
    # Shuffle the exercises to make it random
    # random.shuffle(exercises)
    
    # Return a random subset of exercises (e.g., top 3)
    return exercises
# БД =============================================================




router = Router()

class TrainingStates(StatesGroup):
    select_date = State()
    select_exercise = State()
    select_additional_weight = State()
    select_repetitions = State()
    finish = State()
    edit_choose_exercise = State()
    edit_choose_set = State()
    edit_choose_mode = State()
    edti_mode = State()



def initialize_exercise_data() -> Dict[str, Union[int, Dict]]:
    """
    Инициализирует данные о тренировке
    """
    return {
        'global_set_counter': 1,
        'exercises': {}
    }


def add_exercise(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    exercise_name: str
) -> None:
    """
    Добавляет упражнение к тренировке
    """
    if exercise_id in exercise_data['exercises']:
        return
    exercise_data['exercises'][exercise_id] = {
        'exercise_name': exercise_name,
        'local_set_counter': 1,
        'sets': {}
    }


def add_set(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    weight: int = None,
    repetitions: int = None,
    time: str = None
) -> None:
    """
    Добавляет подход к упражнению
    """
    set_number = exercise_data['exercises'][exercise_id]['local_set_counter']

    exercise_data['exercises'][exercise_id]['sets'][set_number] = {
        'set_number': exercise_data['global_set_counter'],
        'weight': weight,
        'repetitions': repetitions,
        'time': time
    }

    exercise_data['exercises'][exercise_id]['local_set_counter'] += 1
    exercise_data['global_set_counter'] += 1


def update_weight(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    new_weight: int,
    set_number: int = None,
) -> None:
    """
    Обновляет вес
    """
    if set_number is None:
        set_number = exercise_data['exercises'][exercise_id]['local_set_counter'] - 1
    exercise_data['exercises'][exercise_id]['sets'][set_number]['weight'] = new_weight


def update_repetitions(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    new_repetitions: int,
    set_number: int = None,
) -> None:
    """
    Обновляет количество повторений
    """
    if set_number is None:
        set_number = exercise_data['exercises'][exercise_id]['local_set_counter'] - 1
    exercise_data['exercises'][exercise_id]['sets'][set_number]['repetitions'] = new_repetitions


def update_time(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    new_time: str,
    set_number: int = None,
) -> None:
    """
    Обновляет время выполнения упражнения
    """
    if set_number is None:
        set_number = exercise_data['exercises'][exercise_id]['local_set_counter'] - 1
    exercise_data['exercises'][exercise_id]['sets'][set_number]['time'] = new_time


def delete_exercise(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str
) -> None:
    """
    Удаляет упражнение со всеми подходами
    """
    del exercise_data['exercises'][exercise_id]


def delete_set(
    exercise_data: Dict[str, Union[int, Dict]],
    exercise_id: str,
    set_number: str
) -> None:
    """
    Удаляет подход
    """
    del exercise_data['exercises'][exercise_id]['sets'][set_number]
    # Удаляет упражнение, если нет ни одного подхода
    # if not exercise_data['exercises'][exercise_id]['sets']:
    #     del exercise_data['exercises'][exercise_id]



def format_exercise_data(exercise_data):
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
        training_values.append(f"Тренировка {html.bold(date_formatted)} ({html.bold(weekday_name)}):")

    if user_data.get('exercise_data') and user_data.get('exercise_data').get('exercises'):
        training_values.append(format_exercise_data(user_data['exercise_data']))

    if len(training_values) > 0:
        text_list.append("\n".join(training_values))

    cur_values = []
    if user_data.get('exercise') is not None:
        cur_values.append(f"🔹 Упражнение: {html.bold(html.underline(user_data['exercise']))}")

    if user_data.get('weight') is not None:
        cur_values.append(f"🔹 Вес: {html.bold(html.underline(user_data['weight']))} кг")
        
    if user_data.get('repetitions') is not None:
        cur_values.append(f"🔹 Кол-во повторений: {html.bold(html.underline(user_data['repetitions']))}")

    if len(cur_values) > 0:
        text_list.append("Текущие значения:\n" + "\n".join(cur_values))

    # Добавить текст на основе текущего состояния
    state_to_text = {
        "TrainingStates:select_date":               "Выберите дату",
        "TrainingStates:select_exercise":           "Выберите упражнение",
        "TrainingStates:select_additional_weight":  "Выберите доп. вес",
        "TrainingStates:select_repetitions":        "Выберите кол-во повторений",
        "TrainingStates:finish":                    "Что дальше",
        "TrainingStates:edit_choose_exercise":      "Выберите упражнение",
        "TrainingStates:edit_choose_set":           "Выберите подход",
        "TrainingStates:edit_choose_mode":          "Выберите режим",
    }
    current_state = await state.get_state()
    text_list.append(f"⬇️ {state_to_text[current_state]} ⬇️")
    
    return "\n\n".join(text_list)



@router.message(StateFilter(None), Command("training"))
async def cmd_training(message: Message, state: FSMContext) -> None:
    """
    Команда /training
    """
    await state.set_state(TrainingStates.select_date)

    await state.update_data(exercise_data=initialize_exercise_data())
    await state.update_data(most_frequent_exercises=await get_most_frequent_exercises())

    answer = await message.answer(
        text=await get_formatted_state_date(state),
        reply_markup=ikb_select_date,
    )
    await state.update_data(message_id=answer.message_id)




@router.callback_query(
    F.data == 'today',
    TrainingStates.select_date
)
async def selected_date_today(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Инлайн кнопка "Сегодня"
    """
    await state.set_state(TrainingStates.select_exercise)

    await state.update_data(date=datetime.now())

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises = user_data.get('most_frequent_exercises', [])
    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_select_exercise_fab(most_frequent_exercises),
    )



@router.callback_query(
    F.data == 'other_date',
    TrainingStates.select_date
)
async def selected_date_other(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Инлайн кнопка "Другая дата"
    """
    await callback.message.edit_reply_markup(
        reply_markup=await DialogCalendar().start_calendar()
    )



@router.callback_query(dialog_cal_callback.filter())
async def process_dialog_calendar(
    callback: CallbackQuery,
    callback_data: CallbackData,
    state: FSMContext
) -> None:
    """
    Обработка выбора даты в инлайн календаре
    """
    selected, date = await DialogCalendar().process_selection(callback, callback_data)

    if selected:
        await state.set_state(TrainingStates.select_exercise)

        await state.update_data(date=date)

        user_data: Dict[str, Union[int, Dict]] = await state.get_data()
        most_frequent_exercises = user_data.get('most_frequent_exercises', [])
        await callback.message.edit_text(
            text=await get_formatted_state_date(state),
            reply_markup = get_ikb_select_exercise_fab(most_frequent_exercises),
        )
        

    
@router.callback_query(F.data == 'cancel')
async def cancel_trainings(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "❌"("Отмена")
    """
    await state.clear()
    await callback.message.delete()



@router.callback_query(
    TrainingExercisePagination.filter(F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])),
    TrainingStates.select_exercise
)
async def selected_exercise_pagination(
    callback: CallbackQuery,
    callback_data: TrainingExercisePagination,
    state: FSMContext
):
    """
    Пагинация выбора упражнения
    """
    page = int(callback_data.page)
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises = user_data.get('most_frequent_exercises', [])

    if callback_data.action == PaginationAction.PREV:
        page = page - 1 if page > 0 else 0
    elif callback_data.action == PaginationAction.NEXT:
        page = page + 1 if page < len(most_frequent_exercises) - 1 else page

    await callback.message.edit_reply_markup(
        reply_markup = get_ikb_select_exercise_fab(most_frequent_exercises, page),
    )



@router.callback_query(
    TrainingExercisePagination.filter(F.action == PaginationAction.SET),
    TrainingStates.select_exercise
)
async def selected_exercise( 
    callback: CallbackQuery,
    callback_data: TrainingExercisePagination,
    state: FSMContext
):
    """
    Кнопка выбора упражнения
    """
    await state.set_state(TrainingStates.select_additional_weight)

    def get_value_by_key(key, lst):
        for d in lst:
            if key in d:
                return d[key]
        return None

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises = user_data.get('most_frequent_exercises', [])
    exercise_id = int(callback_data.exercise_id)
    exercise_name = get_value_by_key(exercise_id, most_frequent_exercises)
    exercise_data = user_data.get('exercise_data')

    add_exercise(exercise_data, exercise_id, exercise_name)

    await state.update_data(exercise_data=exercise_data)
    await state.update_data(exercise=exercise_name)
    await state.update_data(exercise_id=exercise_id)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(),
    )

    


@router.inline_query(TrainingStates.select_additional_weight)
async def selected_additional_weight(inline_query: InlineQuery, state: FSMContext):
    """
    Инлайн выбор доп. веса: возвращает список значений
    """
    def generate_numbers(substring: str) -> List[float]:
        """
        Генерирует список чисел, которые содержат substring
        """
        numbers = []
        for i in range(0, 30100, 25):
            number = i / 100
            if str(number).find(substring) != -1:
                numbers.append(number)
        return numbers
    
    offset = int(inline_query.offset) if inline_query.offset else 0
    
    results = []
    for number in generate_numbers(inline_query.query):
        results.append(
            InlineQueryResultArticle(
                id=str(number),
                title=f"{number:.2f} кг",
                input_message_content=InputTextMessageContent(
                    message_text = str(number)
                ),
            )
        )
    if len(results) < 50:
        await inline_query.answer(
            results,
            cache_time = 0,
            is_personal=True
        )
    else:
        await inline_query.answer(
            results[offset:offset+50],
            next_offset=str(offset+50),
            cache_time = 0,
            is_personal=True,
        )



@router.message(
    F.via_bot,
    TrainingStates.select_additional_weight
)
async def selected_additional_weight(message: Message, state: FSMContext):
    """
    Инлайн выбор доп. веса: обработка выбранного значения
    """
    await state.set_state(TrainingStates.select_repetitions)

    await state.update_data(weight=float(message.text))
    await message.delete()

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    exercise_data = user_data.get('exercise_data')
    exercise_id = user_data.get('exercise_id')

    add_set(exercise_data, exercise_id, float(message.text))

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_open_inline_search()
    )



@router.inline_query(TrainingStates.select_repetitions)
async def selected_additional_weight(inline_query: InlineQuery, state: FSMContext):
    """
    Инлайн выбор кол-ва повторений: возвращает список значений
    """
    def generate_numbers(substring: str) -> List[float]:
        """
        Генерирует список чисел, которые содержат substring
        """
        numbers = []
        for number in range(0, 101):
            if str(number).find(substring) != -1:
                numbers.append(number)
        return numbers
    
    offset = int(inline_query.offset) if inline_query.offset else 0
    
    results = []
    for number in generate_numbers(inline_query.query):
        results.append(
            InlineQueryResultArticle(
                id=str(number),
                title=f"{number} повторений",
                input_message_content=InputTextMessageContent(
                    message_text = str(number)
                ),
            )
        )
    if len(results) < 50:
        await inline_query.answer(
            results,
            cache_time = 0,
            is_personal=True
        )
    else:
        await inline_query.answer(
            results[offset:offset+50],
            next_offset=str(offset+50),
            cache_time = 0,
            is_personal=True
        )



@router.message(
    F.via_bot,
    TrainingStates.select_repetitions
)
async def selected_additional_weight(message: Message, state: FSMContext):
    """
    Инлайн выбор доп. веса: обработка выбранного значения
    """
    await state.set_state(TrainingStates.finish)

    await state.update_data(repetitions=int(message.text))
    await message.delete()

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    exercise_data = user_data.get('exercise_data')
    exercise_id = user_data.get('exercise_id')

    update_repetitions(exercise_data, exercise_id, int(message.text))
    if user_data.get('date').strftime('%d.%m.%Y') == datetime.now().strftime('%d.%m.%Y'):
        update_time(exercise_data, exercise_id, datetime.now())

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup=ikb_finish_training
    )



@router.callback_query(
    F.data == 'add_exercise',
    TrainingStates.finish
)
async def add_exercise_handler(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Добавить упражнение"
    """
    await state.set_state(TrainingStates.select_exercise)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises = user_data.get('most_frequent_exercises', [])
    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_select_exercise_fab(most_frequent_exercises),
    )



@router.callback_query(
    F.data == 'add_set',
    TrainingStates.finish
)
async def add_set_handler(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Добавить повторение"
    """
    await state.set_state(TrainingStates.select_additional_weight)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(),
    )



@router.callback_query(F.data == 'edit_menu', TrainingStates.finish)
async def edit_sets_handler(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Внести исправления"
    """
    await state.set_state(TrainingStates.edit_choose_exercise)
    
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    exercises = user_data.get('exercise_data').get('exercises')

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_edit_select_exercise_fab(exercises)
    )


@router.callback_query(
    EditTrainingExercisePagination.filter(F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])),
    TrainingStates.edit_choose_exercise
)
async def selected_exercise_pagination(
    callback: CallbackQuery,
    callback_data: TrainingExercisePagination,
    state: FSMContext
):
    """
    Пагинация выбора упражнения
    """
    page = int(callback_data.page)
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    exercises = user_data.get('exercise_data').get('exercises')

    if callback_data.action == PaginationAction.PREV:
        page = page - 1 if page > 0 else 0
    elif callback_data.action == PaginationAction.NEXT:
        page = page + 1 if page < len(exercises) - 1 else page

    await callback.message.edit_reply_markup(
        reply_markup = get_ikb_edit_select_exercise_fab(exercises, page),
    )


@router.callback_query(F.data == 'select_exercise_back', TrainingStates.select_exercise)
@router.callback_query(F.data == 'select_back', TrainingStates.select_additional_weight)
@router.callback_query(F.data == 'select_back', TrainingStates.select_repetitions)
@router.callback_query(F.data == 'edit_menu_back', TrainingStates.edit_choose_exercise)
@router.callback_query(F.data == 'edit_menu_back', TrainingStates.edit_choose_set)
@router.callback_query(F.data == 'edit_menu_back', TrainingStates.edit_choose_mode)
async def edit_back_finish(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Назад" в режиме изменения
    """
    back_state = {
        "TrainingStates:select_exercise": "TrainingStates:finish",
        "TrainingStates:select_additional_weight": "TrainingStates:select_exercise",
        "TrainingStates:select_repetitions": "TrainingStates:select_additional_weight",
        "TrainingStates:edit_choose_exercise": "TrainingStates:finish",
        "TrainingStates:edit_choose_set": "TrainingStates:edit_choose_exercise",
        "TrainingStates:edit_choose_mode": "TrainingStates:edit_choose_set",
    }
    current_state = await state.get_state()
    new_state = back_state[current_state]
    await state.set_state(new_state)

    ikb_by_state = {
        "TrainingStates:finish": ikb_finish_training,
        "TrainingStates:select_exercise": get_ikb_select_exercise_fab,
        "TrainingStates:select_additional_weight": get_ikb_open_inline_search,
        "TrainingStates:edit_choose_exercise": get_ikb_edit_select_exercise_fab,
        # "TrainingStates:edit_choose_set": get_ikb_edit_choose_set_fab,
    }
    new_reply_markup = ikb_by_state[new_state]

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=new_reply_markup() if isinstance(new_reply_markup, Callable) else new_reply_markup
    )


@router.callback_query(
    F.data == 'finish_training',
    TrainingStates.finish
)
async def finish_training(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Завершить тренировку"
    """
    await state.clear()
    await callback.message.delete()