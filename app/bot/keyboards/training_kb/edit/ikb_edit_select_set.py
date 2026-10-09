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

    for i in range(page * page_size, (page + 1) * page_size):
        if i >= len(sets):
            break
        set_id = i + 1
        set_data = sets[i]
        builder.row(
            InlineKeyboardButton(
                text=format_draft_set_to_text(
                    set_data=set_data,
                    set_id=set_id,
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
            text="⬅️ Упражнение ⬅️",
            callback_data="to_edit_menu_exercise",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Удалить все подходы 🗑️",
            callback_data="delete_all_sets",
        )
    )
    return builder.as_markup()


