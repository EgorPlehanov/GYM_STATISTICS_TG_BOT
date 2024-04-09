from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from middlewares import DBSessionMiddleware
from db.models import User
from db.database import async_session_factory
from db.queries import is_user_in_database, create_user



router = Router()
router.message.middleware(DBSessionMiddleware(async_session_factory))



@router.message(StateFilter(None), CommandStart())
async def cmd_training(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """
    Команда /start
    """
    text = ""
    if not await is_user_in_database(session=session, user_id=message.from_user.id):
        text += f"{message.from_user.full_name}, рад что ты присоединился!\n"
        await create_user(session=session, user=User(
            id=message.from_user.id,
            name=message.from_user.full_name,
            chat_id=message.chat.id,
            language_code=message.from_user.language_code,
        ))

    text += "Отправь команду /help, чтобы узнать как использовать бота"

    await message.answer(
        text=text
    )