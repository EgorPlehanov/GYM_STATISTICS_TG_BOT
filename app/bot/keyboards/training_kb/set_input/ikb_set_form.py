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
    has_changes: bool = False,
    edited_set_number: int | None = None,
) -> InlineKeyboardMarkup:
    """Создаёт компактную клавиатуру формы добавления подходов.

    Args:
        exercise_name: выбранное упражнение или None.
        weight: выбранный вес или None.
        repetitions: выбранное число повторений или None.
        sets_count: выбранное число подходов или None.
        can_submit: доступна ли команда добавления или сохранения.
        is_editing: форма редактирует один существующий подход.
        has_changes: изменились ли параметры редактируемого подхода.
        edited_set_number: отображаемый номер редактируемого подхода.

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
        builder.row(
            InlineKeyboardButton(
                text=f"Подход {edited_set_number}" if edited_set_number is not None else "Подход",
                callback_data="edit_form_set",
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
    if is_editing and not has_changes:
        actions = [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="to_edit_menu_set")
        ]
    else:
        actions = [
            InlineKeyboardButton(
                text="❌ Отменить" if is_editing else "Отменить",
                callback_data="to_edit_menu_set" if is_editing else "to_menu",
            )
        ]
    if can_submit and (not is_editing or has_changes):
        actions.append(
            InlineKeyboardButton(
                text="✅ Сохранить" if is_editing else "Добавить",
                callback_data="accept_edit" if is_editing else "accept_addition",
            )
        )
    builder.row(*actions)
    if is_editing:
        builder.row(InlineKeyboardButton(text="🗑️ Удалить подход", callback_data="delete_set"))
    return builder.as_markup()
