from aiogram import Router, html
from aiogram.types import Message
from aiogram.filters import Command, StateFilter



router = Router()



@router.message(StateFilter(None), Command("help"))
async def cmd_training(message: Message) -> None:
    """
    Команда /help
    """
    await message.answer(
        text=(
            f"🤖 {html.bold('Основные команды:')}\n\n"
            f"💪 /training - начать тренировку (доступно в личке бота)\n\n"
            f"📊 /statistics - статистика тренировок\n\n"
            f"📤 /redirect - установить редирект в группу (при вызове в группах и настройки редиректа при вызове в личке бота)\n\n"
            f"📚 /guide - небольшой гайд по функциям бота который поможет тебе освоиться\n\n"
            f"ℹ️ /help - помощь, сейчас ты тут)\n\n"
            f"▶️ /start - запустить бота (доступно в личке бота)\n\n"
        ),
    )

