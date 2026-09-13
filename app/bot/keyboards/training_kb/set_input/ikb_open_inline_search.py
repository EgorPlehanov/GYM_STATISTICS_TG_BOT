from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_ikb_open_inline_search(
    entity_name: str = "",
    back_button_text: str = "Меню",
    back_button_callback_data: str = "to_menu",
    has_next_button: bool = False,
    next_button_text: str = "Вперед",
    next_button_callback_data: str = "",
    has_accept_button: bool = False,
    accept_button_text: str = "Добавить",
    accept_button_callback_data: str = "accept_addition",
    has_delete_set_button: bool = False,
    switch_inline_query: str = "",
) -> InlineKeyboardMarkup:
    """Создает клавиатуру выбора значения через inline search.

    Args:
        entity_name: название выбираемой сущности для текста кнопки.
        back_button_text: текст кнопки возврата.
        back_button_callback_data: callback кнопки возврата.
        has_next_button: добавить кнопку перехода вперед.
        next_button_text: текст кнопки перехода вперед.
        next_button_callback_data: callback кнопки перехода вперед.
        has_accept_button: добавить кнопку подтверждения.
        accept_button_text: текст кнопки подтверждения.
        accept_button_callback_data: callback кнопки подтверждения.
        has_delete_set_button: добавить кнопку удаления подхода.
        switch_inline_query: предзаполненный текст inline search.

    Returns:
        Inline-клавиатура для текущего шага ввода.
    """
    builder = InlineKeyboardBuilder()

    if has_accept_button:
        builder.row(
            InlineKeyboardButton(
                text=f"✅ {accept_button_text.capitalize()} ✅",
                callback_data=accept_button_callback_data,
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=f"🔎 Выбрать {entity_name.lower()} 🔎",
            switch_inline_query_current_chat=switch_inline_query,
        )
    )

    builder.row(
        *[
            InlineKeyboardButton(
                text=(
                    f"⬅️ {back_button_text.capitalize()} "
                    f"{'' if has_next_button else '⬅️'}"
                ),
                callback_data=back_button_callback_data,
            )
        ]
        + (
            [
                InlineKeyboardButton(
                    text=f"{next_button_text.capitalize()} ➡️",
                    callback_data=next_button_callback_data,
                )
            ]
            if has_next_button
            else []
        )
    )

    if has_delete_set_button:
        builder.row(
            InlineKeyboardButton(
                text="🗑️ Удалить подход 🗑️",
                callback_data="delete_set",
            )
        )

    return builder.as_markup()

