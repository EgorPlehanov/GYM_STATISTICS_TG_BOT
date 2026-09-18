"""Меню редактирования и удаления сущностей черновика."""

from copy import deepcopy

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.fsm.training import (
    TrainingFlowStep,
    TrainingStates,
    delete_all_exercise_sets_from_draft,
    delete_all_exercises_from_draft,
    delete_set_from_draft,
    get_training_draft,
    update_set_in_draft,
)
from app.bot.ui.training import is_current_training_callback, transition_training_screen

router = Router()


@router.callback_query(F.data == "to_edit_menu", TrainingStates.menu)
@router.callback_query(F.data == "to_edit_menu", TrainingStates.select_date)
@router.callback_query(F.data == "to_edit_menu", TrainingStates.edit_select_exercise)
async def open_edit_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает меню редактирования текущего draft."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=draft, next_draft=deepcopy(draft),
        next_step=TrainingFlowStep.EDIT_MENU,
    )


@router.callback_query(F.data == "accept_edit", TrainingStates.select_weight)
@router.callback_query(F.data == "accept_edit", TrainingStates.select_repetitions)
@router.callback_query(F.data == "accept_edit", TrainingStates.accept_addition)
async def accept_edit(callback: CallbackQuery, state: FSMContext) -> None:
    """Применяет изменения выбранного подхода в draft."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    update_set_in_draft(
        next_draft, next_draft.edit.exercise_id, next_draft.edit.set_id,
        new_weight=next_draft.selection.weight,
        new_repetitions=next_draft.selection.repetitions,
    )
    next_draft.selection.mode = None
    next_draft.selection.weight = None
    next_draft.selection.repetitions = None
    next_draft.edit.exercise_id = None
    next_draft.edit.exercise_name = None
    next_draft.edit.set_id = None
    next_draft.edit.set_number = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_MENU,
    )


@router.callback_query(F.data == "delete_all_exercises", TrainingStates.edit_select_exercise)
@router.callback_query(F.data == "delete_all_sets", TrainingStates.edit_select_set)
@router.callback_query(F.data == "delete_set", TrainingStates.select_weight)
@router.callback_query(F.data == "delete_set", TrainingStates.select_repetitions)
async def delete_accept(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает typed-подтверждение удаления без сохранения клавиатуры."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.ui.suspended_step = TrainingFlowStep(
        (await state.get_state()).rsplit(":", maxsplit=1)[-1]
    )
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_DELETE,
    )


@router.callback_query(F.data == "delete_cancel", TrainingStates.edit_delete)
async def delete_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает на шаг под подтверждением удаления."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    suspended_step = current_draft.ui.suspended_step
    if suspended_step is None:
        raise ValueError("Для отмены удаления нужен suspended_step")
    next_draft = deepcopy(current_draft)
    next_draft.ui.suspended_step = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft, next_step=suspended_step,
    )


@router.callback_query(F.data == "delete_accepted", TrainingStates.edit_delete)
async def delete_exercises_sets(callback: CallbackQuery, state: FSMContext) -> None:
    """Удаляет подтвержденную сущность из draft."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    exercise_id = next_draft.edit.exercise_id
    set_id = next_draft.edit.set_id
    if exercise_id is None:
        delete_all_exercises_from_draft(next_draft)
    elif set_id is None:
        delete_all_exercise_sets_from_draft(next_draft, exercise_id)
    else:
        delete_set_from_draft(next_draft, exercise_id, set_id)
    if next_draft.ui.current_exercise_id not in {
        exercise.exercise_id for exercise in next_draft.training.exercises
    }:
        next_draft.ui.current_exercise_id = None
        next_draft.ui.current_exercise_name = None
        next_draft.ui.last_weight = None
        next_draft.ui.last_repetitions = None
    next_draft.selection.mode = None
    next_draft.selection.weight = None
    next_draft.selection.repetitions = None
    next_draft.edit.exercise_id = None
    next_draft.edit.exercise_name = None
    next_draft.edit.set_id = None
    next_draft.edit.set_number = None
    next_draft.ui.suspended_step = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_MENU,
    )
