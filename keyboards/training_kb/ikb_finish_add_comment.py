from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder



def get_ikb_finish_add_comment(
    current_comment: bool = None
) -> InlineKeyboardMarkup:
    """
    Фабрика инлайн клавиатуры меню редактирования тренировки
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💪 Продолжить тренировку 💪", callback_data="to_menu"))
    builder.row(InlineKeyboardButton(
        text = f"{'✏️ Исправить' if current_comment else '➕ Добавить'} комментарий 📝",
        switch_inline_query_current_chat = current_comment if current_comment else ""
    ))
    builder.row(InlineKeyboardButton(text="✅ Сохранить и завершить ✅", callback_data="finish"))
    return builder.as_markup()