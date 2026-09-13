from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import BufferedInputFile, Message

from app.bot.client import BotApiClient
from app.bot.formatters.export import get_export_data_file
from app.bot.middlewares import (
    ChatActionMiddleware,
)
from app.bot.utils.user_access import ensure_bot_user

router = Router()
router.message.middleware(ChatActionMiddleware())



@router.message(
    StateFilter(None),
    Command("export_data"),
    flags={'chat_action': 'upload_document'}
)
async def cmd_export_data(message: Message) -> None:
    """
    Команда /export_data
    """
    await ensure_bot_user(message.from_user)

    waitig_answer = await message.answer("🗂️")

    async with BotApiClient() as api_client:
        export_data = await api_client.get_export_data(message.from_user.id)

    file_buffer = get_export_data_file(export_data)
    
    await message.reply_document(
        document = BufferedInputFile(
            file=file_buffer,
            filename="export_data.xlsx"
        ),
        caption = (
            "📄 Файл уже готов!\n"
            "🗄️ Я собрала всю нужную информацию и поместила ее в этот файл!"
        )
    )
    await waitig_answer.delete()

