from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from typing import Dict, Union

from .training_states import TrainingStates
from utils.format_exercise_data import get_formatted_state_date
from keyboards import (
    get_ikb_select_exercise_fab,
    TrainingExercisePagination,
    PaginationAction,
    get_ikb_open_inline_search,
)
from utils.check_acept_addition import check_acept_addition



router = Router()



@router.callback_query(
    F.data == 'add_exercise',
    TrainingStates.menu
)
async def add_exercise_handler(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Добавить упражнение"
    """
    await state.set_state(TrainingStates.select_exercise)
    await state.update_data(mode="add_exercise")

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises = user_data.get('most_frequent_exercises', [])

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_select_exercise_fab(exercise_data=most_frequent_exercises),
    )



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
        reply_markup = get_ikb_select_exercise_fab(
            exercise_data=most_frequent_exercises,
            page=page,
            has_acept_addition_button = await check_acept_addition(state)
        ),
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
    await state.set_state(TrainingStates.select_weight)

    def get_value_by_key(key, lst):
        for d in lst:
            if key in d:
                return d[key]
        return None

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises = user_data.get('most_frequent_exercises', [])

    exercise_data = user_data.get('exercise_data')
    exercise_id = int(callback_data.exercise_id)
    exercise_name = get_value_by_key(exercise_id, most_frequent_exercises)

    await state.update_data(exercise_data=exercise_data)
    await state.update_data(cur_exercise_name=exercise_name)
    await state.update_data(cur_exercise_id=exercise_id)

    back_button_text = {
        "add_exercise": "Упражнение",
        "add_set": "Меню",
    }
    back_button_callback_data = {
        "add_exercise": "to_exercise",
        "add_set": "to_menu",
    }
    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "вес",
            back_button_text=back_button_text.get(user_data.get('mode')),
            back_button_callback_data=back_button_callback_data.get(user_data.get('mode')),
            has_next_button=user_data.get("weight") is not None,
            next_button_text="Повторения",
            next_button_callback_data="to_repetitions",
        ),
    )


@router.callback_query(F.data == "to_exercise", TrainingStates.select_weight)
@router.callback_query(F.data == "to_exercise", TrainingStates.acept_addition)
async def back_to_exercise(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Назад" возврат к выбору упражнения
    """
    await state.set_state(TrainingStates.select_exercise)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises = user_data.get('most_frequent_exercises', [])

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_select_exercise_fab(
            exercise_data = most_frequent_exercises,
            has_next_button = user_data.get("cur_exercise_id") is not None,
            has_acept_addition_button = await check_acept_addition(state)
        ),
    )