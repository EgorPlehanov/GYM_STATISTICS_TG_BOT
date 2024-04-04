from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from typing import List, Dict
import math

from .keyboards_types import PaginationAction



class EditTrainingExercisePagination(CallbackData, prefix='ex_pag'):
    """
    CallbackData для пагинации выбора упражнения
    """
    
    action: PaginationAction
    page: int
    exercise_id: int



def get_ikb_edit_select_exercise_fab(
    exercise_data: Dict[int, str],
    page: int = 0,
    page_size: int = 5
) -> InlineKeyboardMarkup:
    """
    Фабрика для инлайн клавиатуры для выбора упражнения из тренировки
    """
    builder = InlineKeyboardBuilder()
    
    for i in range(page * page_size, (page + 1) * page_size):
        if i >= len(exercise_data):
            break
        builder.row(
            InlineKeyboardButton(
                text=list(exercise_data.values())[i]["exercise_name"],
                callback_data=EditTrainingExercisePagination(
                    action=PaginationAction.SET,
                    page=page,
                    exercise_id=list(exercise_data.keys())[i],
                ).pack()
            )
        )
    builder.row(*([
        InlineKeyboardButton(
            text='⬅️',
            callback_data=EditTrainingExercisePagination(
                action=PaginationAction.PREV,
                page=page,
                exercise_id=-1,
            ).pack()
        )
    ] if page > 0 else []) + ([
        InlineKeyboardButton(
            text='➡️',
            callback_data=EditTrainingExercisePagination(
                action=PaginationAction.NEXT,
                page=page,
                exercise_id=-1,
            ).pack()
        )
    ] if page < math.ceil(len(exercise_data) / page_size) - 1 else []))

    builder.row(InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="edit_menu_back"))
    return builder.as_markup()
