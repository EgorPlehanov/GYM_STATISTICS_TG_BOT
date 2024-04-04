from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



ikb_finish_training = InlineKeyboardMarkup(inline_keyboard = [
    [
        InlineKeyboardButton(text="+ Упражнение 💪", callback_data="add_exercise"),
        InlineKeyboardButton(text="+ Подход 🏋️‍♀️", callback_data="add_set"),
    ],
    [InlineKeyboardButton(text="Внести изменения 📝", callback_data="edit_menu")],
    [InlineKeyboardButton(text="Завершить тренировку 🏁", callback_data="finish_training")],
])
