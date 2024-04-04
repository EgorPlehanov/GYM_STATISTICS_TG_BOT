from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder



def get_ikb_training_menu(
    is_add_edit_button: bool = True
) -> InlineKeyboardMarkup:
    """
    Фабрика инлайн клавиатуры меню тренировки
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        *[InlineKeyboardButton(text="+ Упражнение 🏋️‍♀️", callback_data="add_exercise")] + ([
            InlineKeyboardButton(text="+ Подход 💪", callback_data="add_set")
        ] if is_add_edit_button else [])
    )
    if is_add_edit_button:
        builder.row(InlineKeyboardButton(text="Внести изменения 📝", callback_data="edit_menu"))
        builder.row(InlineKeyboardButton(text="Завершить тренировку 🏁", callback_data="finish_training"))
    else:
        builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"))
    return builder.as_markup()