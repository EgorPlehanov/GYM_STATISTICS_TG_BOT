from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from typing import Dict, Union

from .training_types import TrainingStates
from utils.format_exercise_data import get_formatted_state_date
from keyboards import (
    PaginationAction,
    EditTrainingExercisePagination,
    get_ikb_edit_select_exercise_fab,
    get_ikb_edit_select_set_fab,
)



router = Router()



@router.callback_query(
    F.data == "edit_exercise",
    TrainingStates.edit_menu
)
async def open_edit_exercise(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Редактировать упражнения"
    """
    await state.set_state(TrainingStates.edit_select_exercise)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

    exercises = user_data.get('exercise_data').get('exercises')

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_select_exercise_fab(exercises),
    )



@router.callback_query(
    EditTrainingExercisePagination.filter(
        F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])
    ),
    TrainingStates.edit_select_exercise
)
async def selected_exercise_pagination(
    callback: CallbackQuery,
    callback_data: EditTrainingExercisePagination,
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



@router.callback_query(
    EditTrainingExercisePagination.filter(F.action == PaginationAction.SET),
    TrainingStates.edit_select_exercise
)
async def selected_exercise(
    callback: CallbackQuery,
    callback_data: EditTrainingExercisePagination,
    state: FSMContext
):
    """
    Выбрано упражнение из меню редактирования
    """
    await state.set_state(TrainingStates.edit_select_set)

    await state.update_data(edit_exercise_id=callback_data.exercise_id)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    edit_exercise_name = user_data['exercise_data']['exercises'][callback_data.exercise_id]['exercise_name']

    await state.update_data(edit_exercise_name=edit_exercise_name)

    exercise_sets = user_data['exercise_data']['exercises'][callback_data.exercise_id]['sets']

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_select_set_fab(exercise_sets),
    )



@router.callback_query(
    F.data == "to_edit_menu_exercise",
    TrainingStates.edit_select_set
)
async def back_to_edit_exercise(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Назад"
    """
    await state.set_state(TrainingStates.edit_select_exercise)

    await state.update_data(edit_exercise_id=None)
    await state.update_data(edit_exercise_name=None)

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    exercises = user_data.get('exercise_data').get('exercises')

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_select_exercise_fab(exercises),
    )