from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.bot.client import BotApiClient


async def send_training_result_to_redirect_groups(
    bot: Bot,
    result_text: str,
    telegram_id: int,
    is_update: bool = False,
    is_created: bool = False,
    training_id: int | None = None,
) -> None:
    """Отправляет результат тренировки в группы с включенным редиректом.

    Функция используется после сохранения тренировки в Telegram-сценарии.
    Если тренировка создана впервые, результат отправляется новым сообщением,
    а id сообщения сохраняется через internal API. Если тренировка обновлена,
    бот пытается отредактировать ранее отправленное сообщение. Если старое
    сообщение удалено, результат отправляется повторно, а сохраненный message id
    обновляется или создается заново.

    Args:
        bot: экземпляр aiogram Bot для отправки и редактирования сообщений.
        result_text: уже отформатированный текст результата тренировки.
        telegram_id: Telegram user id пользователя, для которого ищутся группы редиректа.
        is_update: признак обновления существующей тренировки.
        is_created: признак создания новой тренировки.
        training_id: внутренний id сохраненной тренировки. Используется для поиска
            и сохранения связи между тренировкой и сообщением в группе.

    Returns:
        None. Все изменения выполняются через Telegram Bot API и internal API.

    Raises:
        RuntimeError: если `BotApiClient` используется вне async context manager.

    Notes:
        Ошибки TelegramBadRequest при недоступной группе не пробрасываются наружу:
        группа помечается как недоступная через internal API, чтобы следующий
        сценарий не считал редирект гарантированно рабочим.
    """
    async with BotApiClient() as api_client:
        redirect_group_ids = await api_client.get_redirect_group_ids(telegram_id)

        for group_id in redirect_group_ids:
            if is_update:
                group_result_message_id = await api_client.get_training_result_message_id(
                    group_id=group_id,
                    training_id=training_id,
                )
                try:
                    await bot.edit_message_text(
                        text=result_text,
                        chat_id=group_id,
                        message_id=group_result_message_id,
                    )
                except TelegramBadRequest as e:
                    if "same as a current content" in e.message:
                        # Игнорируем повторную отправку сообщения с тем же содержимым.
                        continue

                    # Если старое сообщение удалено из чата, отправляем новое.
                    try:
                        new_group_result_message = await bot.send_message(
                            chat_id=group_id,
                            text=result_text,
                        )
                        is_id_updated = await api_client.update_training_result_message(
                            group_id=group_id,
                            training_id=training_id,
                            new_message_id=new_group_result_message.message_id,
                        )
                        # Если запись о сообщении была удалена из БД, создаем ее заново.
                        if not is_id_updated:
                            await api_client.create_training_result_message(
                                group_id=group_id,
                                training_id=training_id,
                                message_id=new_group_result_message.message_id,
                            )
                    except TelegramBadRequest:
                        # Если бот был удален из чата, помечаем группу как недоступную.
                        await api_client.update_group_bot_banned(
                            group_id=group_id,
                            is_bot_banned=True,
                        )
                continue

            if is_created:
                group_result_message = await bot.send_message(
                    chat_id=group_id,
                    text=result_text,
                )
                await api_client.create_training_result_message(
                    group_id=group_id,
                    training_id=training_id,
                    message_id=group_result_message.message_id,
                )


