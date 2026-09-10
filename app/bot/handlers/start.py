from aiogram import F, Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.utils.user_access import ensure_bot_user

router = Router()
router.message.filter(F.chat.type == "private")



@router.message(StateFilter(None), CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """
    Команда /start
    """
    result = await ensure_bot_user(message.from_user)

    if result.created:
        await message.answer(
            text=(
                f"{message.from_user.first_name}, рад что ты присоединился!\n"
                "Отправь команду /help, чтобы узнать как использовать бота"
            )
        )
    else:
        await message.answer(text="🐆")

