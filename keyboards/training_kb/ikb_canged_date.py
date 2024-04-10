from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from datetime import datetime



def get_ikb_canged_date(
    other_date: datetime
) -> InlineKeyboardMarkup:
    """
    Фабрика инлайн клавиатуры перехода к другой дате
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=f"✅ Сохранить текущую и перейти к {other_date.strftime('%d.%m.%Y')} ✅",
        callback_data="save_and_go"
    ))
    builder.row(InlineKeyboardButton(
        text="✏️ Заменить на текущую ✏️", callback_data="canged_to_current_date"))
    builder.row(InlineKeyboardButton(
        text="⬅️ Меню даты ⬅️", callback_data="to_date_menu"))
    return builder.as_markup()