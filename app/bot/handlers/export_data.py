from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import BufferedInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.middlewares import (
    ChatActionMiddleware,
    DBSessionMiddleware,
)
from app.bot.utils.data_export import get_export_data_file
from app.bot.utils.user_access import ensure_bot_user
from app.db.session import async_session_factory

router = Router()
router.message.middleware(DBSessionMiddleware(async_session_factory))
router.message.middleware(ChatActionMiddleware())



@router.message(
    StateFilter(None),
    Command("export_data"),
    flags={'chat_action': 'upload_document'}
)
async def cmd_export_data(message: Message, session: AsyncSession) -> None:
    """
    Команда /export_data
    """
    await ensure_bot_user(message.from_user)

    waitig_answer = await message.answer("🗂️")

    file_buffer = await get_export_data_file(
        session = session,
        user_id = message.from_user.id
    )
    
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

