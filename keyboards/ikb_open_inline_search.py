from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



def get_ikb_open_inline_search(
    entity_name: str = "",
    back_button_text: str = "Меню",
    back_button_callback_data: str = "to_menu",
    has_next_button: bool = False,
    next_button_text: str = "Вперед",
    next_button_callback_data: str = "",
    has_acept_addition_button: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=f"Выбрать {entity_name}", switch_inline_query_current_chat=""))
    builder.row(
        *[InlineKeyboardButton(text=f"⬅️ {back_button_text}", callback_data=back_button_callback_data)] + ([
            InlineKeyboardButton(text=f"{next_button_text} ➡️", callback_data=next_button_callback_data)
        ] if has_next_button else [])
    )
    if has_acept_addition_button:
        builder.row(InlineKeyboardButton(text="✅ Добавить ✅", callback_data="acept_addition"))
    return builder.as_markup()