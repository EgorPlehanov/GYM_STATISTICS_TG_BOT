"""Проверки доступа пользователя к сценариям Telegram-бота."""

from aiogram.types import User as TelegramUser

from app.bot.client import BotApiClient, EnsureUserResult


async def ensure_bot_user(telegram_user: TelegramUser) -> EnsureUserResult:
    """Создает или обновляет пользователя перед запуском сценария бота.

    Args:
        telegram_user: пользователь из Telegram update.

    Returns:
        результат регистрации пользователя через internal API.

    Эта функция является единой точкой входа для будущей проверки доступа:
    согласие на обработку данных, блокировки, ограничения аккаунта и другие
    условия должны добавляться здесь, а не размазываться по handlers.
    """
    async with BotApiClient() as api_client:
        return await api_client.ensure_user(
            telegram_id=telegram_user.id,
            name=telegram_user.full_name,
            language_code=telegram_user.language_code,
        )
