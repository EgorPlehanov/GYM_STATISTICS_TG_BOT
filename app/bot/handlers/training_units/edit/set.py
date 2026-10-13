"""Выбор и изменение подхода в режиме редактирования."""

from copy import deepcopy

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.fsm.training import (
    TrainingFlowStep,
    TrainingMode,
    TrainingStates,
    get_draft_set_by_local_id,
    get_training_draft,
)
from app.bot.keyboards.keyboards_types import PaginationAction
from app.bot.keyboards.training_kb import EditTrainingSetPagination
from app.bot.ui.training import is_current_training_callback, transition_training_screen

router = Router()


@router.callback_query(
    EditTrainingSetPagination.filter(F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])),
    TrainingStates.edit_select_set,
)
async def selected_set_pagination(
    callback: CallbackQuery, callback_data: EditTrainingSetPagination, state: FSMContext
) -> None:
    """Переключает страницу списка подходов выбранного упражнения."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    page = int(callback_data.page)
    next_draft.ui.edit_set_page = (
        max(page - 1, 0)
        if callback_data.action is PaginationAction.PREV
        else page + 1
    )
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_SELECT_SET,
    )


@router.callback_query(
    EditTrainingSetPagination.filter(F.action == PaginationAction.SET),
    TrainingStates.edit_select_set,
)
async def selected_set(
    callback: CallbackQuery, callback_data: EditTrainingSetPagination, state: FSMContext
) -> None:
    """Открывает выбранный подход для редактирования веса и повторений."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    set_id = callback_data.set_id
    set_data = get_draft_set_by_local_id(next_draft, next_draft.edit.exercise_id, set_id)
    next_draft.edit.set_id = set_id
    next_draft.edit.set_number = set_id
    next_draft.selection.mode = TrainingMode.EDIT_SET.value
    next_draft.selection.exercise_id = next_draft.edit.exercise_id
    next_draft.selection.exercise_name = next_draft.edit.exercise_name
    next_draft.selection.weight = set_data.weight
    next_draft.selection.repetitions = set_data.repetitions
    next_draft.selection.sets_count = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.SET_FORM,
    )


@router.callback_query(F.data == "to_edit_menu_set", TrainingStates.set_form)
async def back_to_edit_set(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает к выбору подхода для редактирования."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.edit.set_id = None
    next_draft.edit.set_number = None
    next_draft.selection.weight = None
    next_draft.selection.repetitions = None
    next_draft.selection.exercise_id = None
    next_draft.selection.exercise_name = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_SELECT_SET,
    )
