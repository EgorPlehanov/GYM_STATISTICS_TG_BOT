from aiogram import Router, F
from aiogram.types import (
    CallbackQuery, Message, InlineQuery,
    InlineQueryResultArticle, InputTextMessageContent
)
from aiogram.fsm.context import FSMContext

from typing import Dict, Union
from sqlalchemy.ext.asyncio import AsyncSession

from .training_types import TrainingStates
from utils.format_exercise_data import get_formatted_state_date
from utils.redirect_result_to_user_group import redirect_result_to_user_group
from keyboards.training_kb import get_ikb_finish_add_comment
from middlewares import DBSessionMiddleware
from db.database import async_session_factory
from db.queries import (
    save_training_data,
    get_user_group_to_redirect,
    update_or_create_user_exercise_rating,
)



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

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()

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



@router.message(TrainingStates.add_comment)
@router.message(F.via_bot, TrainingStates.add_comment)
async def add_comment(message: Message, state: FSMContext):
    """
    Ввод комментария
    """
    await message.delete()

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    user_data['exercise_data']['comment'] = message.text[:2000]

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup = get_ikb_finish_add_comment(
            current_comment = message.text[:2000]
        ),
    )



@router.callback_query(
    F.data == 'finish',
    TrainingStates.add_comment,
)
async def finish(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """
    Инлайн кнопка "Завершить"
    """
    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    exercise_data = user_data.get('exercise_data')

    training_id, is_update, is_create = await save_training_data(
        session=session,
        training_data=exercise_data
    )

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
        session = session,
        result_text = f"@{callback.from_user.username}\n{result_text}",
        redirect_groups_id = await get_user_group_to_redirect(session, callback.from_user.id),
        id_upadate = is_update,
        is_create = is_create,
        training_id = training_id
    )

    await update_or_create_user_exercise_rating(
        session = session,
        user_id = callback.from_user.id,
    )