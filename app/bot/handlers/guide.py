from aiogram import Router, html
from aiogram.types import Message
from aiogram.filters import Command, StateFilter



router = Router()



@router.message(StateFilter(None), Command("guide"))
async def cmd_guide(message: Message) -> None:
    """
    Команда /guide
    """
    await message.answer(
        text=(
            f"🥲 {html.bold('В данный момент гайд недоступен(')}\n"
            f"👨‍💻 Скоро он появится!"
        ),
    )

