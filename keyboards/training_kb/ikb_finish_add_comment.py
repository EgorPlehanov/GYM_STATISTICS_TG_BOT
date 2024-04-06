from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



ikb_finish_add_comment = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton(text="💪 Продолжить тренировку 💪", callback_data="to_menu")],
    [InlineKeyboardButton(text="✅ Завершить ✅", callback_data="finish")],
])
