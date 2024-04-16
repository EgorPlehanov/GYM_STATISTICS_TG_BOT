from aiogram import Router, F
from aiogram.types import Message, PhotoSize

from filters.main_admin import MainAdminFilter



router = Router()
router.message.filter(MainAdminFilter())



@router.message(F.photo[-1].as_("photo"))
async def save_image(message: Message, photo: PhotoSize):
    await message.answer(
        f"photo.file_id:\n{photo.file_id}\n\n"
        f"photo.file_unique_id:\n{photo.file_unique_id}",
    )