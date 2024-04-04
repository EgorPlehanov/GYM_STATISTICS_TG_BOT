from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



ikb_select_date = InlineKeyboardMarkup(inline_keyboard = [
    [
        InlineKeyboardButton(text="Сегодня", callback_data="today"),
        InlineKeyboardButton(text="Другая дата", callback_data="other_date"),
    ],
    [InlineKeyboardButton(text="❌", callback_data="cancel")],
])