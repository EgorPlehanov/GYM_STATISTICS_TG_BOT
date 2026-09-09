from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.bot.client import BotApiClient


async def redirect_result_to_user_group(
    bot: Bot,
    result_text: str,
    telegram_id: int,
    id_upadate: bool = False,
    is_create: bool = False,
    training_id: int = None,
) -> None:
    """
    Отправляет результат в группы для которых пользователь настроил редирект
    """
    async with BotApiClient() as api_client:
        redirect_groups_id = await api_client.get_redirect_group_ids(telegram_id)

        for group_id in redirect_groups_id:
            if id_upadate:
                # если тренировка была обновлена
                group_result_message_id = await api_client.get_training_result_message_id(
                    group_id=group_id,
                    training_id=training_id,
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
                        is_id_updated = await api_client.update_training_result_message(
                            group_id=group_id,
                            training_id=training_id,
                            new_message_id=new_group_result_message.message_id,
                        )
                        # Если запись о сообщении была удалена из бд
                        if not is_id_updated:
                            await api_client.create_training_result_message(
                                group_id=group_id,
                                training_id=training_id,
                                message_id=new_group_result_message.message_id,
                            )
                    except TelegramBadRequest:
                        # если бот был удален из чата
                        await api_client.update_group_bot_banned(
                            group_id=group_id,
                            is_bot_banned=True,
                        )
                continue

            if is_create:
                # если тренировка была создана новая
                group_result_message = await bot.send_message(
                    chat_id = group_id,
                    text = result_text
                )
                await api_client.create_training_result_message(
                    group_id=group_id,
                    training_id=training_id,
                    message_id=group_result_message.message_id,
                )


