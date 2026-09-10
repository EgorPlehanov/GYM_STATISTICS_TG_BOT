import math
from collections.abc import Sequence
from typing import Protocol

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..keyboards_types import PaginationAction


class RedirectGroupButtonData(Protocol):
    """Минимальные данные группы, необходимые для кнопки редиректа."""

    group_id: int
    group_name: str
    is_redirect_to_group: bool



class RedirectGroupPagination(CallbackData, prefix='rg_pag'):
    """
    CallbackData для пагинации RedirectGroup
    """

    action: PaginationAction
    page: int
    redirect_group_id: int



def get_ikb_redirect_groups(
    redirect_groups: Sequence[RedirectGroupButtonData],
    page: int = 0,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    """
    Фабрика инлайн клавиатура для редирект групп
    """
    builder = InlineKeyboardBuilder()

    for group in redirect_groups[page * page_size: (page + 1) * page_size]:
        builder.row(InlineKeyboardButton(
            text = f"{group.group_name}: {'✅' if group.is_redirect_to_group else '⛔'}",
            callback_data = RedirectGroupPagination(
                action=PaginationAction.SET,
                page=page,
                redirect_group_id=str(group.group_id),
            ).pack()
        ))

    builder.row(*([
        InlineKeyboardButton(
            text='⬅️',
            callback_data=RedirectGroupPagination(
                action=PaginationAction.PREV,
                page=page,
                redirect_group_id=-1,
            ).pack()
        )
    ] if page > 0 else []) + ([
        InlineKeyboardButton(
            text='➡️',
            callback_data=RedirectGroupPagination(
                action=PaginationAction.NEXT,
                page=page,
                redirect_group_id=-1,
            ).pack()
        )
    ] if page < math.ceil(len(redirect_groups) / page_size) - 1 else []))

    builder.row(InlineKeyboardButton(text="⬅️ Сохранить и выйти ⬅️", callback_data="redirect_quit"))
    return builder.as_markup()

