from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from middlewares import DBSessionMiddleware
from db.database import async_session_factory
from db.queries import create_user_if_not_exists



router = Router()
router.message.filter(F.chat.type == "private")
router.message.middleware(DBSessionMiddleware(async_session_factory))



@router.message(StateFilter(None), CommandStart())
async def cmd_training(message: Message, state: FSMContext, session: AsyncSession) -> None:
    """
    Команда /start
    """
    if await create_user_if_not_exists(
        session=session,
        user_id=message.from_user.id,
        name=message.from_user.full_name,
        language_code=message.from_user.language_code,
    ):
        await message.answer(
            text=(
                f"{message.from_user.first_name}, рад что ты присоединился!\n"
                "Отправь команду /help, чтобы узнать как использовать бота"
            )
        )