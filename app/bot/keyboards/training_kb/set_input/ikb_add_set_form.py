"""Клавиатура единой формы добавления подходов."""

from decimal import Decimal

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.core.weights import format_weight


def get_ikb_add_set_form(
    *,
    exercise_name: str | None,
    weight: Decimal | None,
    repetitions: int | None,
    sets_count: int | None,
    can_submit: bool,
    is_editing: bool,
) -> InlineKeyboardMarkup:
    """Создаёт компактную клавиатуру формы добавления подходов.

    Args:
        exercise_name: выбранное упражнение или None.
        weight: выбранный вес или None.
        repetitions: выбранное число повторений или None.
        sets_count: выбранное число подходов или None.
        can_submit: доступна ли команда добавления или сохранения.
        is_editing: форма редактирует один существующий подход.

    Returns:
        Inline-клавиатура с полями формы и командами отмены/добавления.
    """
    builder = InlineKeyboardBuilder()
    if is_editing:
        builder.row(
            InlineKeyboardButton(
                text=exercise_name or "Упражнение",
                callback_data="edit_form_exercise",
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text=exercise_name or "Выбрать упражнение",
                callback_data="form_select_exercise",
            )
        )
    if not is_editing:
        builder.row(
            InlineKeyboardButton(
                text=(
                    f"Подходов: {sets_count}"
                    if sets_count is not None
                    else "Подходов: 1"
                ),
                switch_inline_query_current_chat=(
                    f"s{sets_count}" if sets_count is not None else "s"
                ),
            )
        )
    builder.row(
        InlineKeyboardButton(
            text=f"Вес: {format_weight(weight)} кг" if weight is not None else "Вес",
            switch_inline_query_current_chat=(
                f"w{format_weight(weight)}" if weight is not None else "w"
            ),
        ),
        InlineKeyboardButton(
            text=f"Повторы: {repetitions}" if repetitions is not None else "Повторы",
            switch_inline_query_current_chat=f"r{repetitions}" if repetitions is not None else "r",
        ),
    )
    actions = [
        InlineKeyboardButton(
            text="⬅️ Подход" if is_editing else "Отменить",
            callback_data="to_edit_menu_set" if is_editing else "to_menu",
        )
    ]
    if can_submit:
        actions.append(
            InlineKeyboardButton(
                text="Сохранить" if is_editing else "Добавить",
                callback_data="accept_edit" if is_editing else "accept_addition",
            )
        )
    builder.row(*actions)
    if is_editing:
        builder.row(InlineKeyboardButton(text="Удалить", callback_data="delete_set"))
    return builder.as_markup()
