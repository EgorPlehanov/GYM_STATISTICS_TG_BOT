from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter

from asyncio import sleep


router = Router()
router.message.filter(F.chat.type == "private")



@router.message(F.text.startswith('/'), StateFilter(None))
async def default_command_reaction(message: Message):
    await message.answer(text=(
        "🤔 Я не знаю такой команды\n"
        "Отправь команду /help, чтобы узнать как использовать бота"
    ))



@router.message()
async def default_message_reaction(message: Message):
    answer = await message.answer(text=(
        "🤔 Я тебя не понимаю"
    ))

    await sleep(5)
    await message.delete()
    await answer.delete()



@router.callback_query()
async def default_callback_reaction(callback: CallbackQuery):
    await callback.answer(text=(
        "🚫 Эта кнопка уже не активнва)"
    ))