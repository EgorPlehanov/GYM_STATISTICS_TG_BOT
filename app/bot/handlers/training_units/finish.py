"""Добавление комментария и сохранение тренировки."""

from asyncio import sleep
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

from app.bot.api_client.schemas.trainings import BotTrainingSaveResult
from app.bot.client import BotApiClient
from app.bot.fsm.training import (
    TrainingDraft,
    TrainingFlowStep,
    TrainingStates,
    draft_to_bot_training,
    get_training_draft,
    set_draft_training_dates,
)
from app.bot.ui.training import (
    TrainingTransitionResult,
    is_current_training_callback,
    replace_after_backend,
    transition_training_screen,
)

from .redirect_result import (
    delete_removed_training_redirect_messages,
    send_training_result_to_redirect_groups,
)

router = Router()


@router.callback_query(F.data == "finish_training", TrainingStates.menu)
async def finish_training(callback: CallbackQuery, state: FSMContext) -> None:
    """Открывает шаг добавления комментария перед сохранением."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    await transition_training_screen(
        bot=callback.bot, chat_id=callback.message.chat.id, state=state,
        current_draft=draft, next_draft=deepcopy(draft),
        next_step=TrainingFlowStep.ADD_COMMENT,
    )


@router.inline_query(TrainingStates.add_comment)
async def inline_comment(inline_query: InlineQuery) -> None:
    """Возвращает inline-вариант комментария из введенного текста."""
    results = []
    if inline_query.query:
        results.append(
            InlineQueryResultArticle(
                id="comment", title=inline_query.query,
                input_message_content=InputTextMessageContent(message_text=inline_query.query),
            )
        )
    await inline_query.answer(results, cache_time=0, is_personal=True)


@router.message(F.text, TrainingStates.add_comment)
@router.message(F.via_bot, TrainingStates.add_comment)
async def add_comment(message: Message, state: FSMContext) -> None:
    """Сохраняет комментарий только после успешного обновления главного экрана."""
    current_draft = await get_training_draft(state)
    new_comment = message.text[:500]
    if current_draft.training.comment == new_comment:
        return
    next_draft = deepcopy(current_draft)
    next_draft.training.comment = new_comment
    result = await transition_training_screen(
        bot=message.bot, chat_id=message.chat.id, state=state,
        current_draft=current_draft, next_draft=next_draft,
        next_step=TrainingFlowStep.ADD_COMMENT,
    )
    if result is TrainingTransitionResult.APPLIED:
        await message.delete()
    if len(message.text) > 500:
        warning = await message.answer("❗ Комментарий сокращён до 500 символов.")
        await sleep(3)
        await warning.delete()


@router.callback_query(F.data == "finish", TrainingStates.add_comment)
async def finish(callback: CallbackQuery, state: FSMContext) -> None:
    """Сохраняет тренировку и восстанавливает итоговый экран при ошибке Telegram."""
    draft = await get_training_draft(state)
    if not await is_current_training_callback(callback, draft):
        return
    async with BotApiClient() as api_client:
        save_result = await api_client.save_training(
            telegram_id=callback.from_user.id,
            training=draft_to_bot_training(draft),
            replace_training_id=draft.edit.replace_training_id,
        )

    result_draft = deepcopy(draft)
    result_draft.training.training_id = save_result.training_id
    result_draft.edit.replace_training_id = None
    result_draft.edit.original_training_date = None
    set_draft_training_dates(result_draft, save_result.training_dates)
    try:
        await replace_after_backend(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            state=state,
            draft=result_draft,
            step=TrainingFlowStep.RESULT,
        )
    except Exception:
        await _run_post_save_actions(callback, save_result, result_draft)
        raise

    await callback.answer("✅ Тренировка сохранена 💾")
    await _run_post_save_actions(callback, save_result, result_draft)
    await state.clear()


async def _run_post_save_actions(
    callback: CallbackQuery,
    save_result: BotTrainingSaveResult,
    draft: TrainingDraft,
) -> None:
    """Отправляет побочные результаты после фактически сохраненной тренировки."""
    from app.bot.formatters.training import format_training_step

    rendered_result = format_training_step(draft, TrainingFlowStep.RESULT)
    await delete_removed_training_redirect_messages(
        bot=callback.bot,
        deleted_redirect_messages=save_result.deleted_redirect_messages,
    )
    await send_training_result_to_redirect_groups(
        bot=callback.bot,
        result_text=f"@{callback.from_user.username}\n{rendered_result}",
        telegram_id=callback.from_user.id,
        training_id=save_result.training_id,
        outcome=save_result.outcome,
    )
    async with BotApiClient() as api_client:
        await api_client.recalculate_user_rating(callback.from_user.id)
