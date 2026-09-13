from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.formatters.training import get_formatted_state_date
from app.bot.fsm.training import (
    TrainingStates,
    delete_all_exercise_sets_from_draft,
    delete_all_exercises_from_draft,
    delete_set_from_draft,
    get_training_draft,
    has_draft_exercises,
    set_training_draft,
    update_set_in_draft,
)
from app.bot.keyboards.training_kb import (
    get_ikb_edit_menu,
    ikb_edit_accept_delete,
)

router = Router()



@router.callback_query(F.data == "to_edit_menu", TrainingStates.menu)
@router.callback_query(F.data == "to_edit_menu", TrainingStates.select_date)
@router.callback_query(F.data == "to_edit_menu", TrainingStates.edit_select_exercise)
async def open_edit_menu(callback: CallbackQuery, state: FSMContext):
    """Открывает меню редактирования текущей тренировки."""
    await state.set_state(TrainingStates.edit_menu)

    draft = await get_training_draft(state)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_menu(
            has_edit_exercise_button=has_draft_exercises(draft)
        ),
    )



@router.callback_query(F.data == "accept_edit", TrainingStates.select_weight)
@router.callback_query(F.data == "accept_edit", TrainingStates.select_repetitions)
@router.callback_query(F.data == "accept_edit", TrainingStates.accept_addition)
async def accept_edit(callback: CallbackQuery, state: FSMContext):
    """Применяет изменения выбранного подхода в FSM draft."""
    await state.set_state(TrainingStates.edit_menu)

    draft = await get_training_draft(state)

    edit_exercise_id = draft.edit.exercise_id
    edit_set_id = draft.edit.set_id
    new_weight = draft.selection.weight
    new_repetitions = draft.selection.repetitions

    update_set_in_draft(
        draft,
        edit_exercise_id,
        edit_set_id,
        new_weight=new_weight,
        new_repetitions=new_repetitions,
    )

    draft.selection.mode = None
    draft.selection.weight = None
    draft.selection.repetitions = None
    draft.edit.exercise_id = None
    draft.edit.exercise_name = None
    draft.edit.set_id = None
    draft.edit.set_number = None
    await set_training_draft(state, draft)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_menu(
            has_edit_exercise_button=has_draft_exercises(draft)
        ),
    )



@router.callback_query(F.data == "delete_all_exercises", TrainingStates.edit_select_exercise)
@router.callback_query(F.data == "delete_all_sets", TrainingStates.edit_select_set)
@router.callback_query(F.data == "delete_set", TrainingStates.select_weight)
@router.callback_query(F.data == "delete_set", TrainingStates.select_repetitions)
async def delete_accept(callback: CallbackQuery, state: FSMContext):
    """Открывает подтверждение удаления упражнения, всех подходов или одного подхода."""
    state_before_delete = await state.get_state()

    draft = await get_training_draft(state)
    draft.ui.state_before_delete = state_before_delete
    draft.ui.reply_markup_before_delete = callback.message.reply_markup
    await set_training_draft(state, draft)

    await state.set_state(TrainingStates.edit_delete)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=ikb_edit_accept_delete,
    )



@router.callback_query(F.data == "delete_cancel", TrainingStates.edit_delete)
async def delete_cancel(callback: CallbackQuery, state: FSMContext):
    """Отменяет удаление и возвращает пользователя к предыдущему экрану."""
    draft = await get_training_draft(state)
    state_before_delete = draft.ui.state_before_delete
    reply_markup_before_delete = draft.ui.reply_markup_before_delete

    await state.set_state(state_before_delete)

    draft.ui.state_before_delete = None
    draft.ui.reply_markup_before_delete = None
    await set_training_draft(state, draft)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=reply_markup_before_delete,
    )



@router.callback_query(F.data == "delete_accepted", TrainingStates.edit_delete)
async def delete_exercises_sets(callback: CallbackQuery, state: FSMContext):
    """Удаляет выбранную сущность из FSM draft после подтверждения."""
    await state.set_state(TrainingStates.edit_menu)

    draft = await get_training_draft(state)
    edit_exercise_id = draft.edit.exercise_id
    edit_set_id = draft.edit.set_id

    if edit_exercise_id is None:
        delete_all_exercises_from_draft(draft)
    elif edit_set_id is None:
        delete_all_exercise_sets_from_draft(draft, edit_exercise_id)
    else:
        delete_set_from_draft(draft, edit_exercise_id, edit_set_id)

    current_exercise_id = draft.ui.current_exercise_id
    exercise_ids = {exercise.exercise_id for exercise in draft.training.exercises}
    should_clear_current_exercise = current_exercise_id not in exercise_ids

    draft.selection.mode = None
    draft.selection.weight = None
    draft.selection.repetitions = None
    draft.edit.exercise_id = None
    draft.edit.exercise_name = None
    draft.edit.set_id = None
    draft.edit.set_number = None
    draft.ui.state_before_delete = None
    draft.ui.reply_markup_before_delete = None
    if should_clear_current_exercise:
        draft.ui.current_exercise_id = None
        draft.ui.current_exercise_name = None
        draft.ui.last_weight = None
        draft.ui.last_repetitions = None
    await set_training_draft(state, draft)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_menu(
            has_edit_exercise_button=has_draft_exercises(draft)
        ),
    )
    

