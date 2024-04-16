from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command, StateFilter

from sqlalchemy.ext.asyncio import AsyncSession

from middlewares import (
    DBSessionMiddleware,
    ChatActionMiddleware,
)
from db.database import async_session_factory
from utils.data_export import get_export_data_file


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
    file_buffer = await get_export_data_file(
        session = session,
        user_id = message.from_user.id
    )
    await message.reply_document(
        document = BufferedInputFile(
            file=file_buffer,
            filename="export_data.xlsx"
        )
    )