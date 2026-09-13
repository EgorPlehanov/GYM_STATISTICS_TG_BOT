from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.bot.formatters.training import get_formatted_state_date
from app.bot.fsm.training import (
    TrainingStates,
    draft_to_legacy_exercise_sets_data,
    draft_to_legacy_exercises_data,
    get_draft_exercise,
    get_training_draft,
    set_training_draft,
)
from app.bot.keyboards.keyboards_types import PaginationAction
from app.bot.keyboards.training_kb import (
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
    """Открывает выбор упражнения для редактирования."""
    await state.set_state(TrainingStates.edit_select_exercise)

    draft = await get_training_draft(state)
    exercises = draft_to_legacy_exercises_data(draft)

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
    """Переключает страницу списка упражнений в режиме редактирования."""
    page = int(callback_data.page)
    draft = await get_training_draft(state)
    exercises = draft_to_legacy_exercises_data(draft)

    if callback_data.action == PaginationAction.PREV:
        page = page - 1 if page > 0 else 0
    elif callback_data.action == PaginationAction.NEXT:
        page = page + 1 if page < len(exercises) - 1 else page

    await callback.message.edit_reply_markup(
        reply_markup=get_ikb_edit_select_exercise_fab(exercises, page),
    )



@router.callback_query(
    EditTrainingExercisePagination.filter(F.action == PaginationAction.SET),
    TrainingStates.edit_select_exercise
)
async def selected_edit_exercise(
    callback: CallbackQuery,
    callback_data: EditTrainingExercisePagination,
    state: FSMContext
):
    """Сохраняет выбранное упражнение и открывает список его подходов."""
    await state.set_state(TrainingStates.edit_select_set)

    draft = await get_training_draft(state)
    exercise = get_draft_exercise(draft, callback_data.exercise_id)
    edit_exercise_name = exercise.exercise_name

    draft.edit.exercise_id = callback_data.exercise_id
    draft.edit.exercise_name = edit_exercise_name
    await set_training_draft(state, draft)

    exercise_sets = draft_to_legacy_exercise_sets_data(
        draft,
        callback_data.exercise_id,
    )

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_select_set_fab(exercise_sets),
    )



@router.callback_query(
    F.data == "to_edit_menu_exercise",
    TrainingStates.edit_select_set
)
async def back_to_edit_exercise(callback: CallbackQuery, state: FSMContext):
    """Возвращает пользователя к выбору упражнения для редактирования."""
    await state.set_state(TrainingStates.edit_select_exercise)

    draft = await get_training_draft(state)
    draft.edit.exercise_id = None
    draft.edit.exercise_name = None
    await set_training_draft(state, draft)

    exercises = draft_to_legacy_exercises_data(draft)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_edit_select_exercise_fab(exercises),
    )

