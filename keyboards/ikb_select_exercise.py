from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from typing import List, Dict
import math

from .keyboards_types import PaginationAction




class TrainingExercisePagination(CallbackData, prefix='ex_pag'):
    """
    CallbackData для пагинации выбора упражнения
    """

    action: PaginationAction
    page: int
    exercise_id: int



def get_ikb_select_exercise_fab(
    exercise_data: List[Dict[int, str]],
    page: int = 0,
    page_size: int = 5,
    has_next_button: bool = False,
    has_acept_addition_button: bool = False,
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
    builder.row(
        *[InlineKeyboardButton(text="⬅️ Меню", callback_data="to_menu")] + ([
            InlineKeyboardButton(text="Вес ➡️", callback_data="to_weight")
        ] if has_next_button else [])
    )
    if has_acept_addition_button:
        builder.row(InlineKeyboardButton(text="✅ Добавить ✅", callback_data="acept_addition"))
    return builder.as_markup()
