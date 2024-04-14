from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from typing import Dict, Union, List
from sqlalchemy.ext.asyncio import AsyncSession

from .training_types import TrainingStates
from utils.format_exercise_data import get_formatted_state_date
from keyboards.training_kb import ikb_finish_add_comment
from middlewares import DBSessionMiddleware
from db.database import async_session_factory
from db.queries import (
    save_training_data,
    get_user_group_to_redirect,
    create_group_training_result_message,
    get_group_training_result_messages_id,
    update_group_training_result_message_id,
    update_group_is_bot_banned,
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

    await callback.message.edit_text(
        text=await get_formatted_state_date(state),
        reply_markup=ikb_finish_add_comment,
    )



@router.message(TrainingStates.add_comment)
async def add_comment(message: Message, state: FSMContext):
    """
    Ввод комментария
    """
    # await state.update_data(comment=message.text)
    await message.delete()

    user_data: Dict[str, Union[int, Dict]] = await state.get_data()
    user_data['exercise_data']['comment'] = message.text

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=user_data.get('message_id'),
        text=await get_formatted_state_date(state),
        reply_markup = ikb_finish_add_comment,
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



async def redirect_result_to_user_group(
    bot: Bot,
    session: AsyncSession,
    result_text: int,
    redirect_groups_id: List[int],
    id_upadate: bool = False,
    is_create: bool = False,
    training_id: int = None,
) -> None:
    """
    Отправляет результат в группы для которых пользователь настроил редирект
    """
    for group_id in redirect_groups_id:
        if id_upadate:
            # если тренировка была обновлена
            group_result_message_id = await get_group_training_result_messages_id(
                session = session,
                group_id = group_id,
                training_id = training_id
            )
            try:
                await bot.edit_message_text(
                    text = result_text,
                    chat_id = group_id,
                    message_id = group_result_message_id,
                )
            except TelegramBadRequest as e:
                if "same as a current content" in e.message:
                    # иннорировать если сообщение с таким содержанием уже было отправлено
                    continue
                
                # если сообщение было удалено из чата
                try:
                    new_group_result_message = await bot.send_message(
                        chat_id = group_id,
                        text = result_text
                    )
                    is_id_updated = await update_group_training_result_message_id(
                        session = session,
                        group_id = group_id,
                        training_id = training_id,
                        new_message_id = new_group_result_message.message_id
                    )
                    # Если запись о сообщении была удалена из бд 
                    if not is_id_updated:
                        await create_group_training_result_message(
                            session = session,
                            group_id = group_id,
                            training_id = training_id,
                            message_id = new_group_result_message.message_id
                        )
                except TelegramBadRequest:
                    # если бот был удален из чата
                    await update_group_is_bot_banned(
                        session = session,
                        group_id = group_id,
                        is_bot_banned = True,
                    )

        if is_create:
            # если тренировка была создана новая
            group_result_message = await bot.send_message(
                chat_id = group_id,
                text = result_text
            )
            await create_group_training_result_message(
                session = session,
                group_id = group_id,
                training_id = training_id,
                message_id = group_result_message.message_id
            )
