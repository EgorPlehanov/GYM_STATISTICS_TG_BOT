from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PhotoSize
from aiogram.filters import StateFilter

from asyncio import sleep


router = Router()
router.message.filter(F.chat.type == "private")



# @router.message(F.photo[-1].as_("photo"))
# async def save_image(message: Message, photo: PhotoSize):
#     await message.answer(
#         f"photo.file_id: {photo.file_id}\n"
#         f"photo.file_unique_id: {photo.file_unique_id}",
#     )



@router.message(F.text.startswith('/'), StateFilter(None))
async def default_command_reaction(message: Message):
    await message.answer(text=(
        "🤔 Я не знаю такой команды\n"
        "Отправь команду /help, чтобы узнать как использовать бота"
    ))



@router.message(~F.text.startswith('/'))
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