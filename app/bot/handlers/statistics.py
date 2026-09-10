from aiogram import Router, html
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.middlewares import DBSessionMiddleware
from app.bot.utils.format_user_exercise_rating import format_user_exercise_rating
from app.bot.utils.user_access import ensure_bot_user
from app.db.session import async_session_factory
from app.domain.statistics.service import get_user_exercise_rating

router = Router()
router.message.middleware(DBSessionMiddleware(async_session_factory))



@router.message(StateFilter(None), Command("statistics"))
async def cmd_statistics(message: Message, session: AsyncSession) -> None:
    """
    Команда /statistics
    """
    await ensure_bot_user(message.from_user)

    statistics = await get_user_exercise_rating(
        session = session,
        user_id = message.from_user.id
    )
    if len(statistics) == 0:
        text = "🏆 Добавляй тренировки и тут будут появляться твои лучшие результаты!"
    else:
        text = (
            f"{format_user_exercise_rating(statistics)}\n"
            f"🗄️ {html.italic('Выгрузить все данные о тренировках:')} /export_data"
        )

    await message.answer(
        text = text
    )

