from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



ikb_edit_acept_delete = InlineKeyboardMarkup(inline_keyboard = [[
    InlineKeyboardButton(text="✅ Удалить ✅", callback_data="delete_acepted"),
    InlineKeyboardButton(text="❌ Отмена ❌", callback_data="delete_cancel")
]])