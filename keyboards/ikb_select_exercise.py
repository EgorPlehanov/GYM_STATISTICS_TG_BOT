from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from typing import List, Dict, Union
import math

from .keyboards_types import PaginationAction




class TrainingExercisePagination(CallbackData, prefix='ex_pag'):
    action: PaginationAction
    page: int
    exercise_id: int



def get_ikb_select_exercise_fab(
    exercise_data: List[Dict[int, str]],
    page: int = 0,
    page_size: int = 5
) -> InlineKeyboardMarkup:
    """
    Фабрика для создания инлайн клавиатуры для выбора упражнения
    """
    builder = InlineKeyboardBuilder()
    
    for i in range(page * page_size, (page + 1) * page_size):
        if i >= len(exercise_data):
            break
        builder.row(
            InlineKeyboardButton(
                text=list(exercise_data[i].values())[0],
                callback_data=TrainingExercisePagination(
                    action=PaginationAction.SET,
                    page=page,
                    exercise_id=list(exercise_data[i].keys())[0],
                ).pack()
            )
        )
    builder.row(*([
        InlineKeyboardButton(
            text='⬅️',
            callback_data=TrainingExercisePagination(
                action=PaginationAction.PREV,
                page=page,
                exercise_id=-1,
            ).pack()
        )
    ] if page > 0 else []) + ([
        InlineKeyboardButton(
            text='➡️',
            callback_data=TrainingExercisePagination(
                action=PaginationAction.NEXT,
                page=page,
                exercise_id=-1,
            ).pack()
        )
    ] if page < math.ceil(len(exercise_data) / page_size) - 1 else []))
    builder.row(InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="select_exercise_back"))
    return builder.as_markup()
