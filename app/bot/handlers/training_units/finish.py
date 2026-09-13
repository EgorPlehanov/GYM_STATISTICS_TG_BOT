from asyncio import sleep
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from app.bot.client import BotApiClient
from app.bot.formatters.training import get_formatted_state_date
from app.bot.fsm.training import (
    TrainingStates,
    draft_to_bot_training,
    get_training_draft,
    set_training_draft,
)
from app.bot.keyboards.training_kb import get_ikb_finish_add_comment

from .redirect_result import send_training_result_to_redirect_groups

router = Router()



@router.callback_query(
    F.data == 'finish_training',
    TrainingStates.menu
)
async def finish_training(callback: CallbackQuery, state: FSMContext):
    """Открывает шаг добавления комментария перед сохранением тренировки."""
    await state.set_state(TrainingStates.add_comment)

    draft = await get_training_draft(state)

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_finish_add_comment(
            current_comment=draft.training.comment
        ),
    )



@router.inline_query(TrainingStates.add_comment)
async def inline_comment(inline_query: InlineQuery):
    """Возвращает inline-вариант комментария из введенного текста."""
    await inline_query.answer(
        [
            InlineQueryResultArticle(
                id = str(1),
                title = inline_query.query,
                input_message_content = InputTextMessageContent(
                    message_text = inline_query.query
                ),
            )
        ] if inline_query.query else [],
        cache_time = 0,
        is_personal = True
    )



@router.message(F.text, TrainingStates.add_comment)
@router.message(F.via_bot, TrainingStates.add_comment)
async def add_comment(message: Message, state: FSMContext):
    """Сохраняет комментарий в FSM draft и обновляет сообщение тренировки."""
    await message.delete()

    new_comment = message.text[:500]

    draft = await get_training_draft(state)

    if draft.training.comment == new_comment:
        return

    draft.training.comment = new_comment
    await set_training_draft(state, draft)

    user_data: dict[str, Any] = await state.get_data()

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get("message_id"),
        text=await get_formatted_state_date(state),
        reply_markup=get_ikb_finish_add_comment(
            current_comment=new_comment
        ),
    )
    if len(message.text) > 500:
        warning = await message.answer(
            text="❗ Комментарий сокращён до 500 символов."
        )
        await sleep(3)
        await warning.delete()
    


@router.callback_query(
    F.data == 'finish',
    TrainingStates.add_comment,
)
async def finish(callback: CallbackQuery, state: FSMContext):
    """Сохраняет тренировку, отправляет редирект в группы и запускает пересчет рейтинга."""
    draft = await get_training_draft(state)
    await set_training_draft(state, draft)

    async with BotApiClient() as api_client:
        save_result = await api_client.save_training(
            telegram_id=callback.from_user.id,
            training=draft_to_bot_training(draft),
        )

    training_id = save_result.training_id
    is_update = save_result.updated
    is_created = save_result.created

    result_text = await get_formatted_state_date(state, is_result=True)
    await callback.message.edit_text(
        text=result_text,
    )
    await callback.answer(
        text="✅ Тренировка сохранена 💾",
    )
    await callback.message.answer("Красава жестко!")
    await state.clear()

    await send_training_result_to_redirect_groups(
        bot=callback.message.bot,
        result_text=f"@{callback.from_user.username}\n{result_text}",
        telegram_id=callback.from_user.id,
        is_update=is_update,
        is_created=is_created,
        training_id=training_id,
    )

    async with BotApiClient() as api_client:
        await api_client.recalculate_user_rating(callback.from_user.id)

