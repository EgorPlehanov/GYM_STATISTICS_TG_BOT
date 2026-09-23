"""Точка входа Telegram-бота."""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import (
    bot_member,
    default_reaction,
    error,
    export_data,
    guide,
    help,
    main_admin,
    redirect,
    start,
    statistics,
    training,
    user_member,
)
from app.bot.readiness import clear_bot_readiness, notify_admin_and_mark_bot_ready
from app.core.config import config


async def main() -> None:
    """Запускает Telegram-бота в режиме polling."""
    clear_bot_readiness()
    bot = Bot(
        token=config.TG_BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_routers(
        main_admin.router,
        start.router,
        help.router,
        guide.router,
        bot_member.router,
        user_member.router,
        redirect.router,
        training.router,
        statistics.router,
        export_data.router,
        default_reaction.router,
        error.router,
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await notify_admin_and_mark_bot_ready(
        bot,
        admin_chat_id=int(config.MAIN_ADMIN_ID.get_secret_value()),
        app_env=config.APP_ENV,
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


