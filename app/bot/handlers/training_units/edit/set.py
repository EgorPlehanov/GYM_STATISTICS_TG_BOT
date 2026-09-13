from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.formatters.training import get_formatted_state_date
from app.bot.fsm.training import (
    TrainingMode,
    TrainingStates,
    accept_button_by_mode,
    check_accept_addition,
    get_draft_exercise,
    get_draft_set_by_local_id,
    get_training_draft,
    get_weight_repetitions_modes_values_from_draft,
    set_training_draft,
)
from app.bot.keyboards.keyboards_types import PaginationAction
from app.bot.keyboards.training_kb import (
    EditTrainingSetPagination,
    get_ikb_edit_select_set_fab,
    get_ikb_open_inline_search,
)

router = Router()



@router.callback_query(
    EditTrainingSetPagination.filter(
        F.action.in_([PaginationAction.NEXT, PaginationAction.PREV])
    ),
    TrainingStates.edit_select_set,
)
async def selected_set_pagination(
    callback: CallbackQuery,
    callback_data: EditTrainingSetPagination,
    state: FSMContext,
):
    """Переключает страницу списка подходов выбранного упражнения."""
    page = int(callback_data.page)
    draft = await get_training_draft(state)
    edit_exercise_id = draft.edit.exercise_id
    exercise_sets = get_draft_exercise(draft, edit_exercise_id).sets

    if callback_data.action == PaginationAction.PREV:
        page = page - 1 if page > 0 else 0
    elif callback_data.action == PaginationAction.NEXT:
        page = page + 1 if page < len(exercise_sets) - 1 else page

    await callback.message.edit_reply_markup(
        reply_markup=get_ikb_edit_select_set_fab(exercise_sets, page),
    )


    
@router.callback_query(
    EditTrainingSetPagination.filter(F.action == PaginationAction.SET),
    TrainingStates.edit_select_set,
)
async def selected_set(
    callback: CallbackQuery,
    callback_data: EditTrainingSetPagination,
    state: FSMContext,
):
    """Открывает выбранный подход для редактирования веса и повторений."""
    await state.set_state(TrainingStates.select_weight)

    set_id = callback_data.set_id

    draft = await get_training_draft(state)
    edit_exercise_id = draft.edit.exercise_id
    set_data = get_draft_set_by_local_id(draft, edit_exercise_id, set_id)

    draft.edit.set_id = set_id
    draft.edit.set_number = set_data.set_number
    draft.selection.mode = TrainingMode.EDIT_SET.value
    draft.selection.weight = set_data.weight
    draft.selection.repetitions = set_data.repetitions
    await set_training_draft(state, draft)

    accept_button = accept_button_by_mode.get(TrainingMode.EDIT_SET)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_open_inline_search(
            entity_name="вес",
            back_button_text="Подход",
            back_button_callback_data="to_edit_menu_set",
            has_next_button=True,
            next_button_text="Повторения",
            next_button_callback_data="to_repetitions",
            has_accept_button=await check_accept_addition(state),
            accept_button_text=accept_button.text,
            accept_button_callback_data=accept_button.callback_data,
            has_delete_set_button=True,
            switch_inline_query=get_weight_repetitions_modes_values_from_draft(
                draft,
                is_weight=True,
            ),
        ),
    )



@router.callback_query(
    F.data == "to_edit_menu_set",
    TrainingStates.select_weight,
)
async def back_to_edit_set(callback: CallbackQuery, state: FSMContext):
    """Возвращает пользователя к выбору подхода для редактирования."""
    await state.set_state(TrainingStates.edit_select_set)

    draft = await get_training_draft(state)
    draft.edit.set_id = None
    draft.edit.set_number = None
    draft.selection.weight = None
    draft.selection.repetitions = None
    await set_training_draft(state, draft)

    edit_exercise_id = draft.edit.exercise_id
    exercise_sets = get_draft_exercise(draft, edit_exercise_id).sets

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_select_set_fab(exercise_sets),
    )

