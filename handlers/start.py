from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext



router = Router()



@router.message(StateFilter(None), Command("start"))
async def cmd_training(message: Message, state: FSMContext) -> None:
    """
    Команда /training
    """
    answer = await message.answer(
        text="Отправьте команду /training, чтобы начать тренировку",
    )