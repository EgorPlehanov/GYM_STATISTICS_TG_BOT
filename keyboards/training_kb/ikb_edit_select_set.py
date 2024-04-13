from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from typing import  Dict
import math

from ..keyboards_types import PaginationAction
from utils.formate_set_data_text import format_set_data_to_text



class EditTrainingSetPagination(CallbackData, prefix='ed_set_pag'):
    """
    CallbackData для пагинации выбора упражнения
    """
    
    action: PaginationAction
    page: int
    set_id: int



def get_ikb_edit_select_set_fab(
    exercise_sets_data: Dict[int, Dict[str, int]],
    page: int = 0,
    page_size: int = 5
) -> InlineKeyboardMarkup:
    """
    Фабрика для инлайн клавиатуры для выбора подхода упражнения из тренировки
    """
    builder = InlineKeyboardBuilder()
    
    for i in range(page * page_size, (page + 1) * page_size):
        if i >= len(exercise_sets_data):
            break
        builder.row(
            InlineKeyboardButton(
                text=format_set_data_to_text(list(exercise_sets_data.values())[i]),
                callback_data=EditTrainingSetPagination(
                    action=PaginationAction.SET,
                    page=page,
                    set_id=list(exercise_sets_data.keys())[i],
                ).pack()
            )
        )
    builder.row(*([
        InlineKeyboardButton(
            text='⬅️',
            callback_data=EditTrainingSetPagination(
                action=PaginationAction.PREV,
                page=page,
                set_id=-1,
            ).pack()
        )
    ] if page > 0 else []) + ([
        InlineKeyboardButton(
            text='➡️',
            callback_data=EditTrainingSetPagination(
                action=PaginationAction.NEXT,
                page=page,
                set_id=-1,
            ).pack()
        )
    ] if page < math.ceil(len(exercise_sets_data) / page_size) - 1 else []))
    builder.row(InlineKeyboardButton(text="⬅️ Упражнение ⬅️", callback_data="to_edit_menu_exercise"))
    builder.row(InlineKeyboardButton(text="🗑️ Удалить все подходы 🗑️", callback_data="delete_all_sets"))
    return builder.as_markup()
