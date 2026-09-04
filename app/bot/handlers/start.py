from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.client import BotApiClient

router = Router()
router.message.filter(F.chat.type == "private")



@router.message(StateFilter(None), CommandStart())
async def cmd_training(message: Message, state: FSMContext) -> None:
    """
    Команда /start
    """
    async with BotApiClient() as api_client:
        result = await api_client.ensure_user(
            telegram_id=message.from_user.id,
            name=message.from_user.full_name,
            language_code=message.from_user.language_code,
        )

    if result.created:
        await message.answer(
            text=(
                f"{message.from_user.first_name}, рад что ты присоединился!\n"
                "Отправь команду /help, чтобы узнать как использовать бота"
            )
        )
    else:
        await message.answer(text="🐆")

