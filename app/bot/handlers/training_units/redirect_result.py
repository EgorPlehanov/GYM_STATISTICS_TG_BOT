from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from app.bot.api_client.schemas.trainings import BotTrainingSaveOutcome
from app.bot.client import BotApiClient
from app.bot.telegram.message_operations import (
    ControlledMessageOperationResult,
    edit_controlled_message_text,
)


async def send_training_result_to_redirect_groups(
    bot: Bot,
    result_text: str,
    telegram_id: int,
    training_id: int,
    outcome: BotTrainingSaveOutcome,
) -> None:
    """Синхронизирует результат сохраненной тренировки с redirect-группами.

    Args:
        bot: экземпляр aiogram Bot для операций с Telegram-сообщениями.
        result_text: отформатированный текст результата тренировки.
        telegram_id: Telegram user id владельца тренировки.
        training_id: внутренний id сохраненной тренировки.
        outcome: семантический результат сохранения тренировки.

    Returns:
        None. Связи сообщений обновляются через internal API после успешной отправки.

    Raises:
        TelegramBadRequest: при неизвестной ошибке Telegram-запроса.
        TelegramRetryAfter: при превышении лимита Telegram.
        TelegramNetworkError: при сетевой ошибке.
        TelegramServerError: при ошибке Telegram 5xx.
    """
    if outcome is BotTrainingSaveOutcome.UNCHANGED:
        return

    async with BotApiClient() as api_client:
        redirect_group_ids = await api_client.get_redirect_group_ids(telegram_id)
        for group_id in redirect_group_ids:
            try:
                if outcome is BotTrainingSaveOutcome.CREATED:
                    await _send_and_upsert_training_result_message(
                        bot=bot,
                        api_client=api_client,
                        group_id=group_id,
                        training_id=training_id,
                        result_text=result_text,
                    )
                    continue

                await _update_or_restore_training_result_message(
                    bot=bot,
                    api_client=api_client,
                    group_id=group_id,
                    training_id=training_id,
                    result_text=result_text,
                )
            except TelegramForbiddenError:
                await api_client.update_group_bot_banned(
                    group_id=group_id,
                    is_bot_banned=True,
                )


async def _update_or_restore_training_result_message(
    *,
    bot: Bot,
    api_client: BotApiClient,
    group_id: int,
    training_id: int,
    result_text: str,
) -> None:
    """Редактирует известный результат или создает его новый экземпляр."""
    message_id = await api_client.get_training_result_message_id(
        group_id=group_id,
        training_id=training_id,
    )
    if message_id is None:
        await _send_and_upsert_training_result_message(
            bot=bot,
            api_client=api_client,
            group_id=group_id,
            training_id=training_id,
            result_text=result_text,
        )
        return

    operation_result = await edit_controlled_message_text(
        bot=bot,
        chat_id=group_id,
        message_id=message_id,
        text=result_text,
    )
    if operation_result is ControlledMessageOperationResult.MESSAGE_UNAVAILABLE:
        await _send_and_upsert_training_result_message(
            bot=bot,
            api_client=api_client,
            group_id=group_id,
            training_id=training_id,
            result_text=result_text,
        )


async def _send_and_upsert_training_result_message(
    *,
    bot: Bot,
    api_client: BotApiClient,
    group_id: int,
    training_id: int,
    result_text: str,
) -> None:
    """Отправляет результат и сохраняет id только после успешной отправки."""
    message = await bot.send_message(chat_id=group_id, text=result_text)
    await api_client.upsert_training_result_message(
        group_id=group_id,
        training_id=training_id,
        message_id=message.message_id,
    )


