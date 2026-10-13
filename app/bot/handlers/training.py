"""Входные команды и общие переходы сценария тренировки."""

from copy import deepcopy

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.client import BotApiClient
from app.bot.fsm.training import (
    TrainingDraft,
    TrainingDraftData,
    TrainingFlowStep,
    TrainingStates,
    bot_training_start_context_to_suggestions,
    flow_step_from_state,
    get_training_draft,
)
from app.bot.middlewares import ChatActionMiddleware, UserChatLockMiddleware
from app.bot.ui.training import (
    delete_training_message,
    is_current_training_callback,
    show_or_recover_target,
    start_training_screen,
    transition_training_screen,
)
from app.bot.utils.user_access import ensure_bot_user

from .training_units import (
    accept_router,
    add_set_form_router,
    edit_menu_router,
    edit_select_exercise_router,
    edit_select_set_router,
    finish_add_comment_router,
    select_date_router,
    select_exercise_router,
)

router = Router()
router.message.filter(F.chat.type == "private")
router.message.middleware(ChatActionMiddleware())
training_flow_lock = UserChatLockMiddleware()
router.message.outer_middleware(training_flow_lock)
router.callback_query.outer_middleware(training_flow_lock)
router.include_routers(
    select_date_router,
    select_exercise_router,
    add_set_form_router,
    accept_router,
    edit_menu_router,
    edit_select_exercise_router,
    edit_select_set_router,
    finish_add_comment_router,
)


@router.message(Command("training"))
async def cmd_training(message: Message, state: FSMContext) -> None:
    """Создает новый draft или предлагает продолжить незавершенную тренировку."""
    await ensure_bot_user(message.from_user)
    try:
        draft = await get_training_draft(state)
    except KeyError:
        await _start_new_training(message, state)
    else:
        current_step = flow_step_from_state(await state.get_state())
        if current_step is TrainingFlowStep.RESULT:
            await show_or_recover_target(
                bot=message.bot,
                chat_id=message.chat.id,
                state=state,
                draft=draft,
                step=TrainingFlowStep.RESULT,
            )
            await state.clear()
        else:
            if current_step is not TrainingFlowStep.RESUME_PROMPT:
                draft.ui.suspended_step = current_step

            await show_or_recover_target(
                bot=message.bot,
                chat_id=message.chat.id,
                state=state,
                draft=draft,
                step=TrainingFlowStep.RESUME_PROMPT,
            )

    await message.delete()


@router.message(Command("cancel"), StateFilter(TrainingStates))
async def cancel_training_by_command(message: Message, state: FSMContext) -> None:
    """Аварийно очищает сценарий тренировки из любого его состояния."""
    draft = await get_training_draft(state)
    await state.clear()
    await delete_training_message(
        bot=message.bot,
        chat_id=message.chat.id,
        message_id=draft.ui.message_id,
    )
    await message.answer("❌ Тренировка отменена.")
    await message.delete()


@router.callback_query(F.data == "cancel", StateFilter(TrainingStates))
async def cancel_training_by_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Отменяет тренировку по кнопке главного интерфейса."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    await state.clear()
    await delete_training_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=draft.ui.message_id,
    )
    await callback.answer("❌ Тренировка отменена.")


@router.callback_query(F.data == "to_menu", TrainingStates.select_date)
@router.callback_query(F.data == "to_menu", TrainingStates.select_exercise)
@router.callback_query(F.data == "to_menu", TrainingStates.set_form)
@router.callback_query(F.data == "to_menu", TrainingStates.edit_menu)
@router.callback_query(F.data == "to_menu", TrainingStates.add_comment)
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает в меню, не применяя переход при удаленном интерфейсе."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = deepcopy(current_draft)
    next_draft.selection.mode = None
    next_draft.selection.exercise_id = None
    next_draft.selection.exercise_name = None
    next_draft.selection.weight = None
    next_draft.selection.repetitions = None
    next_draft.selection.sets_count = None
    next_draft.ui.exercise_selection_return_step = None
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.MENU,
    )


@router.callback_query(F.data == "resume_continue", TrainingStates.resume_prompt)
async def resume_training(callback: CallbackQuery, state: FSMContext) -> None:
    """Возвращает пользователя на шаг, сохраненный перед resume_prompt."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    suspended_step = current_draft.ui.suspended_step
    if suspended_step is None:
        raise ValueError("У resume_prompt отсутствует suspended_step")
    next_draft = deepcopy(current_draft)
    next_draft.ui.suspended_step = None
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=suspended_step,
    )


@router.callback_query(F.data == "resume_discard", TrainingStates.resume_prompt)
async def discard_training_draft(callback: CallbackQuery, state: FSMContext) -> None:
    """Удаляет старый draft только после успешной замены resume_prompt."""
    current_draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, current_draft):
        return
    next_draft = TrainingDraft(
        training=TrainingDraftData(training_id=None, training_date=None),
    )
    next_draft.suggestions = deepcopy(current_draft.suggestions)
    await transition_training_screen(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        state=state,
        current_draft=current_draft,
        next_draft=next_draft,
        next_step=TrainingFlowStep.SELECT_DATE,
    )


async def _start_new_training(message: Message, state: FSMContext) -> None:
    """Загружает стартовые подсказки и отправляет первый экран без partial FSM."""
    async with BotApiClient() as api_client:
        start_context = await api_client.get_training_start_context(
            telegram_id=message.from_user.id,
            page_size=15,
            last_training_count=12,
        )

    draft = TrainingDraft(training=TrainingDraftData(training_id=None, training_date=None))
    draft.suggestions = bot_training_start_context_to_suggestions(start_context)
    try:
        await start_training_screen(
            bot=message.bot,
            chat_id=message.chat.id,
            state=state,
            draft=draft,
        )
    except Exception:
        await state.clear()
        raise
