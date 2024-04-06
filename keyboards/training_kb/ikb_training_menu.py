from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder



def get_ikb_training_menu(
    is_add_edit_button: bool = True,
    is_add_add_set_button: bool = False
) -> InlineKeyboardMarkup:
    """
    Фабрика инлайн клавиатуры меню тренировки
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        *[InlineKeyboardButton(text="+ Упражнение 🏋️‍♀️", callback_data="add_exercise")] + ([
            InlineKeyboardButton(text="+ Подход 💪", callback_data="add_set")
        ] if is_add_add_set_button else [])
    )
    if is_add_edit_button:
        builder.row(InlineKeyboardButton(text="📝 Внести исправления 📝", callback_data="to_edit_menu"))
        builder.row(InlineKeyboardButton(text="🏁 Завершить тренировку 🏁", callback_data="finish_training"))
    else:
        builder.row(InlineKeyboardButton(text="❌ Отменить тренировку ❌", callback_data="cancel"))
    return builder.as_markup()