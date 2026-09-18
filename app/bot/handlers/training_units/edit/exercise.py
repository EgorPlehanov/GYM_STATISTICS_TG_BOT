"""Выбор упражнения в режиме редактирования тренировки."""

from copy import deepcopy

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.fsm.training import (
    TrainingFlowStep,
    TrainingStates,
    get_draft_exercise,
    get_training_draft,
)
from app.bot.keyboards.keyboards_types import PaginationAction
from app.bot.keyboards.training_kb import EditTrainingExercisePagination
from app.bot.ui.training import is_current_training_callback, transition_training_screen

router = Router()


@router.callback_query(F.data == "edit_exercise", TrainingStates.edit_menu)
async def open_edit_exercise(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает выбор упражнения для редактирования."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.ui.edit_exercise_page = 0
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_SELECT_EXERCISE,
    )


@router.callback_query(
    EditTrainingExercisePagination.filter(
        F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])
    ),
    TrainingStates.edit_select_exercise,
)
async def selected_exercise_pagination(
    callback: CallbackQuery, callback_data: EditTrainingExercisePagination, state: FSMContext
) -> None:
    """Переключает страницу выбора упражнения."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    page = int(callback_data.page)
    next_draft.ui.edit_exercise_page = (
        max(page - 1, 0)
        if callback_data.action is PaginationAction.PREV
        else page + 1
    )
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_SELECT_EXERCISE,
    )


@router.callback_query(
    EditTrainingExercisePagination.filter(F.action == PaginationAction.SET),
    TrainingStates.edit_select_exercise,
)
async def selected_edit_exercise(
    callback: CallbackQuery, callback_data: EditTrainingExercisePagination, state: FSMContext
) -> None:
    """Выбирает упражнение и открывает список его подходов."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    exercise = get_draft_exercise(next_draft, callback_data.exercise_id)
    next_draft.edit.exercise_id = callback_data.exercise_id
    next_draft.edit.exercise_name = exercise.exercise_name
    next_draft.ui.edit_set_page = 0
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_SELECT_SET,
    )


@router.callback_query(F.data == "to_edit_menu_exercise", TrainingStates.edit_select_set)
async def back_to_edit_exercise(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает к выбору упражнения для редактирования."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.edit.exercise_id = None
    next_draft.edit.exercise_name = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_SELECT_EXERCISE,
    )
