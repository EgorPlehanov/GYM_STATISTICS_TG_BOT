import math

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.formatters.training import format_draft_set_to_text
from app.bot.fsm.training.draft import TrainingDraftSet

from ...keyboards_types import PaginationAction


class EditTrainingSetPagination(CallbackData, prefix="ed_set_pag"):
    """CallbackData для пагинации выбора подхода."""

    action: PaginationAction
    page: int
    set_id: int


def get_ikb_edit_select_set_fab(
    sets: list[TrainingDraftSet],
    page: int = 0,
    page_size: int = 5,
    exercise_name: str | None = None,
) -> InlineKeyboardMarkup:
    """Фабрика inline-клавиатуры выбора подхода из текущего draft.

    Args:
        sets: подходы выбранного упражнения в порядке отображения.
        page: текущая страница пагинации.
        page_size: количество подходов на странице.

    Returns:
        Inline-клавиатура выбора подхода для редактирования.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=exercise_name or "Упражнение",
            callback_data="to_edit_menu_exercise",
        )
    )

    for i in range(page * page_size, (page + 1) * page_size):
        if i >= len(sets):
            break
        set_id = i + 1
        set_data = sets[i]
        builder.row(
            InlineKeyboardButton(
                text=(
                    f"{set_id} · "
                    f"{format_draft_set_to_text(set_data, include_set_number=False)}"
                ),
                callback_data=EditTrainingSetPagination(
                    action=PaginationAction.SET,
                    page=page,
                    set_id=set_id,
                ).pack()
            )
        )
    builder.row(
        *(
            [
                InlineKeyboardButton(
                    text="←",
                    callback_data=EditTrainingSetPagination(
                        action=PaginationAction.PREV,
                        page=page,
                        set_id=-1,
                    ).pack(),
                )
            ]
            if page > 0
            else []
        )
        + (
            [
                InlineKeyboardButton(
                    text="→",
                    callback_data=EditTrainingSetPagination(
                        action=PaginationAction.NEXT,
                        page=page,
                        set_id=-1,
                    ).pack(),
                )
            ]
            if page < math.ceil(len(sets) / page_size) - 1
            else []
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="to_edit_menu_exercise",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Удалить упражнение",
            callback_data="delete_exercise_selected",
        )
    )
    return builder.as_markup()


