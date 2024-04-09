from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext



router = Router()



@router.message(StateFilter(None), Command("help"))
async def cmd_training(message: Message, state: FSMContext) -> None:
    """
    Команда /help
    """

    await message.answer(
        text=(
            f"Отправь команду /training, чтобы начать тренировку!"
        ),
    )