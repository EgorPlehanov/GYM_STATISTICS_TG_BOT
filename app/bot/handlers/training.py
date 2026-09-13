from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.filters.callback_data import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.client import BotApiClient
from app.bot.formatters.training import get_formatted_state_date
from app.bot.fsm.training import (
    TrainingDraft,
    TrainingDraftData,
    get_training_draft,
    has_draft_exercises,
    set_training_draft,
)
from app.bot.keyboards.training_kb import (
    get_ikb_select_date,
    get_ikb_training_menu,
)
from app.bot.middlewares import (
    ChatActionMiddleware,
)
from app.bot.utils.user_access import ensure_bot_user

from .training_units import (
    TrainingStates,
    accept_router,
    edit_menu_router,
    edit_select_exercise_router,
    edit_select_set_router,
    finish_add_comment_router,
    select_date_router,
    select_exercise_router,
    select_repetitions_router,
    select_sets_count_router,
    select_weight_router,
)

router = Router()
router.message.filter(F.chat.type == "private")
router.message.middleware(ChatActionMiddleware())
router.include_routers(
    select_date_router,
    select_exercise_router,
    select_weight_router,
    select_repetitions_router,
    select_sets_count_router,
    accept_router,
    edit_menu_router,
    edit_select_exercise_router,
    edit_select_set_router,
    finish_add_comment_router,
)



@router.message(StateFilter(None), Command("training"))
async def cmd_training(message: Message, state: FSMContext) -> None:
    """
    Команда /training
    """
    await ensure_bot_user(message.from_user)

    await state.set_state(TrainingStates.select_date)

    async with BotApiClient() as api_client:
        start_context = await api_client.get_training_start_context(
            telegram_id=message.from_user.id,
            page_size=15,
            last_training_count=12,
        )

    draft = TrainingDraft(
        training=TrainingDraftData(training_id=None, training_date=None),
    )
    draft.suggestions.most_frequent_exercises = [
        {
            "id": exercise.id,
            "name": exercise.name,
            "description": exercise.description,
        }
        for exercise in start_context.most_frequent_exercises
    ]
    draft.suggestions.weight_repetitions_modes = start_context.weight_repetitions_modes
    await set_training_draft(state, draft)

    answer = await message.answer(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_select_date(is_back_to_menu=False),
    )
    draft.ui.message_id = answer.message_id
    await set_training_draft(state, draft)



@router.callback_query(F.data == 'to_menu', TrainingStates.select_date)
@router.callback_query(F.data == 'to_menu', TrainingStates.select_exercise)
@router.callback_query(F.data == 'to_menu', TrainingStates.select_weight)
@router.callback_query(F.data == 'to_menu', TrainingStates.acept_addition)
@router.callback_query(F.data == 'to_menu', TrainingStates.edit_menu)
@router.callback_query(F.data == 'to_menu', TrainingStates.add_comment)
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Назад" возврат в меню
    """
    await state.set_state(TrainingStates.menu)

    draft = await get_training_draft(state)
    draft.selection.mode = None
    draft.selection.exercise_id = None
    draft.selection.exercise_name = None
    draft.selection.weight = None
    draft.selection.repetitions = None
    draft.selection.sets_count = None
    await set_training_draft(state, draft)

    last_weight = str(draft.ui.last_weight or "").rstrip("0").rstrip(".")
    last_repetitions = draft.ui.last_repetitions or ""

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_training_menu(
            is_add_edit_button=has_draft_exercises(draft),
            is_add_add_set_button=draft.selection.exercise_id is not None,
            repeat_set_button_text=f"{last_weight}×{last_repetitions}",
        ),
    )



@router.callback_query(F.data == 'cancel', TrainingStates.select_date)
@router.callback_query(F.data == 'cancel', TrainingStates.menu)
async def cancel_trainings(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "❌"("Отмена")
    """
    await state.clear()
    await callback.message.delete()

    await callback.message.answer("Слабак🫵, попробуй ещё раз 🤣")


