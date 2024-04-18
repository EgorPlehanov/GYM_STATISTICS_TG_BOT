from aiogram import Router, html
from aiogram.types import Message
from aiogram.filters import Command, StateFilter

from sqlalchemy.ext.asyncio import AsyncSession

from middlewares import DBSessionMiddleware
from db.database import async_session_factory
from db.queries import get_user_exercise_rating
from utils.format_user_exercise_rating import format_user_exercise_rating


router = Router()
router.message.middleware(DBSessionMiddleware(async_session_factory))



@router.message(StateFilter(None), Command("statistics"))
async def cmd_statistics(message: Message, session: AsyncSession) -> None:
    """
    Команда /statistics
    """
    statistics = await get_user_exercise_rating(
        session = session,
        user_id = message.from_user.id
    )
    await message.answer(
        text = (
            f"{format_user_exercise_rating(statistics)}\n"
            f"🗄️ {html.italic('Выгрузить все данные о тренировках:')} /export_data" if len(statistics) > 0 else ''
        )
    )