from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder



def get_ikb_select_date(
    is_back_to_menu: bool = True
) -> InlineKeyboardMarkup:
    """
    Фабрика инлайн клавиатуры выбора даты
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Сегодня 📅", callback_data="today"),
        InlineKeyboardButton(text="Другая дата 🗓️", callback_data="other_date"),
    )
    if is_back_to_menu:
        builder.row(InlineKeyboardButton(text="⬅️ Меню исправления ⬅️", callback_data="to_edit_menu"))
    else:
        builder.row(InlineKeyboardButton(text="❌ Отменить тренировку ❌", callback_data="cancel"))
    return builder.as_markup()