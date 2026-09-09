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
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.client import BotApiClient
from app.bot.keyboards.training_kb import get_ikb_finish_add_comment
from app.bot.middlewares import DBSessionMiddleware
from app.bot.utils.format_training_data import get_formatted_state_date
from app.bot.utils.redirect_result_to_user_group import redirect_result_to_user_group
from app.db.session import async_session_factory
from app.domain.ratings.service import update_or_create_user_exercise_rating

from .training_types import TrainingStates

router = Router()
router.callback_query.middleware(DBSessionMiddleware(async_session_factory))



@router.callback_query(
    F.data == 'finish_training',
    TrainingStates.menu
)
async def finish_training(callback: CallbackQuery, state: FSMContext):
    """
    Инлайн кнопка "Завершить тренировку"
    """
    await state.set_state(TrainingStates.add_comment)

    user_data: dict[str, Any] = await state.get_data()

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_finish_add_comment(
            current_comment = user_data.get('exercise_data').get('comment')
        ),
    )



@router.inline_query(TrainingStates.add_comment)
async def inline_exercise(inline_query: InlineQuery):
    """
    Инлайн выбор упражнения: возвращает список значений
    """
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
    """
    Ввод комментария
    """
    await message.delete()

    new_comment = message.text[:500]

    user_data: dict[str, Any] = await state.get_data()
    
    if user_data['exercise_data']['comment'] == new_comment:
        return
    
    user_data['exercise_data']['comment'] = new_comment

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_finish_add_comment(
            current_comment = new_comment
        ),
    )
    if len(message.text) > 500:
        warning = await message.answer(
            text = "❗ Комментарий сокращён до 500 символов."
        )
        await sleep(3)
        await warning.delete()
    


@router.callback_query(
    F.data == 'finish',
    TrainingStates.add_comment,
)
async def finish(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Инлайн кнопка "Завершить"
    """
    user_data: dict[str, Any] = await state.get_data()
    exercise_data = user_data.get('exercise_data')

    async with BotApiClient() as api_client:
        save_result = await api_client.save_training(exercise_data)

    training_id = save_result.training_id
    is_update = save_result.updated
    is_create = save_result.created

    result_text = await get_formatted_state_date(state, is_result=True)
    await callback.message.edit_text(
        text = result_text,
    )
    await callback.answer(
        text = "✅ Тренировка сохранена 💾",
    )
    await callback.message.answer("Красава жестко!")
    await state.clear()

    await redirect_result_to_user_group(
        bot = callback.message.bot,
        result_text = f"@{callback.from_user.username}\n{result_text}",
        telegram_id=callback.from_user.id,
        id_upadate = is_update,
        is_create = is_create,
        training_id = training_id
    )

    await update_or_create_user_exercise_rating(
        session = session,
        user_id = callback.from_user.id,
    )

