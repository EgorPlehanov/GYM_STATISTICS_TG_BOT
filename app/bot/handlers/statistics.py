from aiogram import Router, html
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

from app.bot.client import BotApiClient
from app.bot.utils.format_user_exercise_rating import format_user_exercise_rating
from app.bot.utils.user_access import ensure_bot_user

router = Router()



@router.message(StateFilter(None), Command("statistics"))
async def cmd_statistics(message: Message) -> None:
    """
    Команда /statistics
    """
    await ensure_bot_user(message.from_user)

    async with BotApiClient() as api_client:
        statistics = await api_client.get_user_exercise_rating(message.from_user.id)

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

