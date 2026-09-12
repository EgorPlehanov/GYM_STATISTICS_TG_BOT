from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder



def get_ikb_edit_menu(has_edit_exercise_button: bool = False) -> InlineKeyboardMarkup:
    """
    Фабрика инлайн клавиатуры меню редактирования тренировки
    """
    builder = InlineKeyboardBuilder()
    if has_edit_exercise_button:
        builder.row(InlineKeyboardButton(text="✏️ Упражнение 💪", callback_data="edit_exercise"))
    builder.row(InlineKeyboardButton(text="✏️ Дата 🗓️", callback_data="edit_date"))
    builder.row(InlineKeyboardButton(text="⬅️ Меню ⬅️", callback_data="to_menu"))
    return builder.as_markup()

