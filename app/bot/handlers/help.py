from aiogram import Router, html
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

router = Router()


@router.message(StateFilter(None), Command("help"))
async def cmd_training(message: Message) -> None:
    """Отправляет список основных команд бота."""
    await message.answer(
        text=(
            f"🤖 {html.bold('Основные команды:')}\n\n"
            f"💪 /training - начать тренировку (доступно в личке бота)\n\n"
            f"📊 /statistics - статистика тренировок\n\n"
            "📤 /redirect - установить редирект в группу "
            "(при вызове в группе) или настроить его в личке бота\n\n"
            f"📚 /guide - небольшой гайд по функциям бота который поможет тебе освоиться\n\n"
            f"ℹ️ /help - помощь, сейчас ты тут)\n\n"
            f"▶️ /start - запустить бота (доступно в личке бота)\n\n"
        ),
    )

