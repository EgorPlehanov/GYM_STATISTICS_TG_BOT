from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder



def get_ikb_acept_addition(
    mode: str = "add_exercise",
) -> InlineKeyboardMarkup:
    """
    Фабрика инлайн клавиатуры подтверждения добавления упражнения/подхода
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Добавить ✅", callback_data="acept_addition"))
    builder.row(InlineKeyboardButton(text="✏️ Изменить повторения 🔁", callback_data="to_repetitions"))
    builder.row(InlineKeyboardButton(text="✏️ Изменить вес ⚖️", callback_data="to_weight"))
    if mode == "add_exercise":
        builder.row(InlineKeyboardButton(text="✏️ Изменить упражнение 🏋", callback_data="to_exercise"))
    return builder.as_markup()