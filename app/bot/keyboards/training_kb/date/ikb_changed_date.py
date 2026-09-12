from datetime import date

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_ikb_changed_date(
    other_date: date,
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
        text="✏️ Заменить на текущую ✏️", callback_data="changed_to_current_date"))
    builder.row(InlineKeyboardButton(
        text="⬅️ Меню даты ⬅️", callback_data="to_date_menu"))
    return builder.as_markup()

