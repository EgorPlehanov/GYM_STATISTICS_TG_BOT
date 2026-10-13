"""Меню редактирования и удаления сущностей черновика."""

from copy import deepcopy

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.fsm.training import (
    TrainingDeletionContext,
    TrainingDeletionView,
    TrainingFlowStep,
    TrainingStates,
    delete_selected_sets_from_draft,
    get_draft_exercise,
    get_training_draft,
    update_set_in_draft,
)
from app.bot.keyboards.training_kb.edit.ikb_edit_delete import (
    EditDeleteExerciseCallback,
    EditDeleteSetCallback,
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
    next_draft = deepcopy(draft)
    next_draft.ui.calendar_year = None
    next_draft.ui.calendar_month = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_MENU,
    )


@router.callback_query(F.data == "accept_edit", TrainingStates.set_form)
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
    next_draft.selection.exercise_id = None
    next_draft.selection.exercise_name = None
    next_draft.edit.exercise_id = None
    next_draft.edit.exercise_name = None
    next_draft.edit.set_id = None
    next_draft.edit.set_number = None
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_MENU,
    )


@router.callback_query(F.data == "open_delete", TrainingStates.edit_menu)
@router.callback_query(F.data == "delete_all_exercises", TrainingStates.edit_select_exercise)
@router.callback_query(F.data == "delete_exercise_selected", TrainingStates.edit_select_set)
@router.callback_query(F.data == "delete_set", TrainingStates.set_form)
async def delete_accept(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает отложенное удаление с предвыбранными целями при необходимости."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    deletion = TrainingDeletionContext()
    if callback.data == "delete_all_exercises":
        deletion.selected_set_local_ids = [
            set_data.local_id
            for exercise in next_draft.training.exercises
            for set_data in exercise.sets
        ]
        deletion.return_step = TrainingFlowStep.EDIT_SELECT_EXERCISE
    elif callback.data == "delete_exercise_selected":
        exercise = get_draft_exercise(next_draft, next_draft.edit.exercise_id)
        deletion.view = TrainingDeletionView.SETS
        deletion.opened_exercise_id = exercise.exercise_id
        deletion.selected_set_local_ids = [set_data.local_id for set_data in exercise.sets]
        deletion.return_step = TrainingFlowStep.EDIT_SELECT_SET
    elif callback.data == "delete_set":
        exercise = get_draft_exercise(next_draft, next_draft.edit.exercise_id)
        deletion.view = TrainingDeletionView.SETS
        deletion.opened_exercise_id = exercise.exercise_id
        deletion.selected_set_local_ids = [exercise.sets[next_draft.edit.set_id - 1].local_id]
        deletion.return_step = TrainingFlowStep.SET_FORM
    next_draft.deletion = deletion
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_DELETE,
    )


@router.callback_query(F.data == "delete_back", TrainingStates.edit_delete)
async def delete_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Закрывает режим удаления без применения выбранных целей."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    return_step = next_draft.deletion.return_step
    next_draft.deletion = TrainingDeletionContext()
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft, next_step=return_step,
    )


@router.callback_query(F.data == "delete_apply", TrainingStates.edit_delete)
async def delete_exercises_sets(callback: CallbackQuery, state: FSMContext) -> None:
    """Применяет выбранные удаления к черновику одной операцией."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    deleted_count = delete_selected_sets_from_draft(
        next_draft, set(next_draft.deletion.selected_set_local_ids)
    )
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
    next_draft.selection.exercise_id = None
    next_draft.selection.exercise_name = None
    next_draft.edit.exercise_id = None
    next_draft.edit.exercise_name = None
    next_draft.edit.set_id = None
    next_draft.edit.set_number = None
    next_draft.deletion = TrainingDeletionContext()
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft, next_step=TrainingFlowStep.MENU,
    )
    await callback.answer(f"🗑️ Удалено: {deleted_count} подходов")


@router.callback_query(EditDeleteExerciseCallback.filter(), TrainingStates.edit_delete)
async def change_delete_exercises(
    callback: CallbackQuery,
    callback_data: EditDeleteExerciseCallback,
    state: FSMContext,
) -> None:
    """Переключает упражнение или страницу в режиме удаления."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    deletion = next_draft.deletion
    if callback_data.action == "prev":
        deletion.exercise_page = max(callback_data.page - 1, 0)
    elif callback_data.action == "next":
        deletion.exercise_page = callback_data.page + 1
    elif callback_data.action == "toggle_all":
        selected = set(deletion.selected_set_local_ids)
        all_local_ids = {
            set_data.local_id
            for exercise in next_draft.training.exercises
            for set_data in exercise.sets
        }
        deletion.selected_set_local_ids = sorted(
            selected - all_local_ids if all_local_ids <= selected else selected | all_local_ids
        )
    elif callback_data.action == "open":
        deletion.view = TrainingDeletionView.SETS
        deletion.opened_exercise_id = callback_data.exercise_id
        deletion.set_page = 0
    elif callback_data.action == "toggle":
        exercise = get_draft_exercise(next_draft, callback_data.exercise_id)
        selected = set(deletion.selected_set_local_ids)
        local_ids = {set_data.local_id for set_data in exercise.sets}
        deletion.selected_set_local_ids = sorted(
            selected - local_ids if local_ids <= selected else selected | local_ids
        )
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_DELETE,
    )


@router.callback_query(EditDeleteSetCallback.filter(), TrainingStates.edit_delete)
async def change_delete_sets(
    callback: CallbackQuery,
    callback_data: EditDeleteSetCallback,
    state: FSMContext,
) -> None:
    """Переключает подход или страницу в режиме удаления."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    deletion = next_draft.deletion
    if callback_data.action == "prev":
        deletion.set_page = max(callback_data.page - 1, 0)
    elif callback_data.action == "next":
        deletion.set_page = callback_data.page + 1
    elif callback_data.action == "toggle":
        selected = set(deletion.selected_set_local_ids)
        if callback_data.local_id in selected:
            selected.remove(callback_data.local_id)
        else:
            selected.add(callback_data.local_id)
        deletion.selected_set_local_ids = sorted(selected)
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_DELETE,
    )


@router.callback_query(F.data == "delete_back_to_exercises", TrainingStates.edit_delete)
async def delete_back_to_exercises(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает к упражнениям, сохраняя текущие отметки удаления."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.deletion.view = TrainingDeletionView.EXERCISES
    next_draft.deletion.opened_exercise_id = None
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_DELETE,
    )


@router.callback_query(F.data == "delete_confirm", TrainingStates.edit_delete)
async def delete_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает экран окончательного подтверждения удаления."""
    await _change_deletion_view(callback, state, TrainingDeletionView.CONFIRM)


@router.callback_query(F.data == "delete_confirm_cancel", TrainingStates.edit_delete)
async def delete_confirm_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает из подтверждения к экрану, с которого оно было открыто."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.deletion.view = (
        TrainingDeletionView.SETS
        if next_draft.deletion.opened_exercise_id is not None
        else TrainingDeletionView.EXERCISES
    )
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_DELETE,
    )


async def _change_deletion_view(
    callback: CallbackQuery,
    state: FSMContext,
    view: TrainingDeletionView,
) -> None:
    """Перерисовывает режим удаления с новым представлением."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.deletion.view = view
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.EDIT_DELETE,
    )
