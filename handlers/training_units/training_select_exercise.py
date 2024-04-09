from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from typing import Dict, Union, List
from collections import namedtuple

from .training_types import (
    TrainingStates,
    TrainingMode,
    exercise_button_by_mode
)
from utils.format_exercise_data import get_formatted_state_date
from keyboards.training_kb import (
    get_ikb_select_exercise_fab,
    TrainingExercisePagination,
    PaginationAction,
    get_ikb_open_inline_search,
)
from utils.check_acept_addition import check_acept_addition
from db.models import Exercise



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
    await state.update_data(mode=TrainingMode.ADD_EXERCISE)

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
            has_acept_addition_button = await check_acept_addition(state),
            select_exercise_id=user_data.get("cur_exercise_id")
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

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    most_frequent_exercises: List[Exercise] = user_data.get('most_frequent_exercises', [])

    exercise_id = int(callback_data.exercise_id)
    exercise = next(e for e in most_frequent_exercises if e.id == exercise_id)

    # Перемещаем выбранное упражнение в начало списка
    most_frequent_exercises.remove(exercise)
    most_frequent_exercises.insert(0, exercise)

    await state.update_data(cur_exercise_name=exercise.name)
    await state.update_data(cur_exercise_id=exercise_id)

    Button = namedtuple("back_button", ["text", "callback_data"])
    
    back_button: Button = exercise_button_by_mode.get(user_data.get('mode'))

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_open_inline_search(
            entity_name = "вес",
            back_button_text=back_button.text,
            back_button_callback_data=back_button.callback_data,
            has_next_button=user_data.get("weight") is not None,
            next_button_text="Повторения",
            next_button_callback_data="to_repetitions",
            has_delete_set_button = user_data.get("mode") == TrainingMode.EDIT_SET
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
            has_acept_addition_button = await check_acept_addition(state),
            select_exercise_id=user_data.get("cur_exercise_id")
        ),
    )