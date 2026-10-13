from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_ikb_edit_menu(has_edit_exercise_button: bool = False) -> InlineKeyboardMarkup:
    """Создает компактное меню редактирования тренировки."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✏️ Дата 🗓️", callback_data="edit_date"))
    if has_edit_exercise_button:
        builder.row(
            InlineKeyboardButton(text="✏️ Упражнения", callback_data="edit_exercise"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data="open_delete"),
        )
    builder.row(InlineKeyboardButton(text="⬅️ Меню", callback_data="to_menu"))
    return builder.as_markup()

