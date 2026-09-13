from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

ikb_edit_accept_delete = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Удалить ✅", callback_data="delete_accepted"),
            InlineKeyboardButton(text="❌ Отмена ❌", callback_data="delete_cancel"),
        ]
    ],
)

