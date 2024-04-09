import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.bot import DefaultBotProperties

from config_reader import config
from handlers import (
    start,
    help,
    training,
)
from db.queries.core import create_tables_async, create_tables_sync



async def main():
    bot = Bot(
        token=config.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    dp.include_routers(
        start.router,
        help.router,
        training.router
    )

    # Пропускаем необработанные при отключенном боте сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



if __name__ == '__main__':
    asyncio.run(main())
    # asyncio.run(create_tables_async())
    # create_tables_sync()