from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



def get_ikb_open_inline_search(
    back_callback_data: str = "select_back"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать", switch_inline_query_current_chat="")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data=back_callback_data)],
    ])