"""Ввод количества повторений."""

from copy import deepcopy

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from app.bot.fsm.training import TrainingFlowStep, TrainingStates, get_training_draft
from app.bot.training_ui import (
    TrainingTransitionResult,
    is_current_training_callback,
    transition_training_screen,
)

router = Router()
r_repetitions = r"^\s*\d+\s*$"


@router.inline_query(TrainingStates.select_repetitions)
async def inline_repetitions(inline_query: InlineQuery, state: FSMContext) -> None:
    """Возвращает inline-подсказки для выбора количества повторений."""
    offset = int(inline_query.offset) if inline_query.offset else 0
    results = [
        InlineQueryResultArticle(
            id=str(number), title=f"{number} повторений",
            input_message_content=InputTextMessageContent(message_text=str(number)),
        )
        for number in range(0, 1001)
        if inline_query.query in str(number)
    ]
    await inline_query.answer(
        results if len(results) < 50 else results[offset : offset + 50],
        next_offset="" if len(results) < 50 else str(offset + 50),
        cache_time=0, is_personal=True,
    )


@router.message(F.via_bot, TrainingStates.select_repetitions)
@router.message(F.text.regexp(r_repetitions), TrainingStates.select_repetitions)
async def selected_repetitions(message: Message, state: FSMContext) -> None:
    """Сохраняет повторения после успешного показа подтверждения."""
    current_draft = await get_training_draft(state)
    next_draft = deepcopy(current_draft)
    next_draft.selection.repetitions = int(message.text)
    result = await transition_training_screen(
        bot=message.bot, chat_id=message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.ACCEPT_ADDITION,
    )
    if result is TrainingTransitionResult.APPLIED:
        await message.delete()


@router.callback_query(F.data == "to_repetitions", TrainingStates.select_weight)
@router.callback_query(F.data == "to_repetitions", TrainingStates.select_sets_count)
@router.callback_query(F.data == "to_repetitions", TrainingStates.accept_addition)
async def to_repetitions(callback: CallbackQuery, state: FSMContext) -> None:
    """Переводит сценарий к выбору количества повторений."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=draft, next_draft=deepcopy(draft),
        next_step=TrainingFlowStep.SELECT_REPETITIONS,
    )
