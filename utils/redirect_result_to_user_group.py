from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from sqlalchemy.ext.asyncio import AsyncSession

from typing import List

from db.queries import (
    create_group_training_result_message,
    get_group_training_result_messages_id,
    update_group_training_result_message_id,
    update_group_is_bot_banned,
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
            continue

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
