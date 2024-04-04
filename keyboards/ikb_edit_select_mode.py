from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



ikb_edit_menu_mode = InlineKeyboardMarkup(inline_keyboard = [
    [
        InlineKeyboardButton(text="Удалить 🗑️", callback_data="edit_menu_delete"),
        InlineKeyboardButton(text="Редактировать ✏️", callback_data="edit_menu_edit"),
    ],
    [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="edit_menu_back")],
])
