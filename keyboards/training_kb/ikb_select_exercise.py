from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from typing import List, Dict
import math

from .keyboards_types import PaginationAction
from db.models import Exercise



class TrainingExercisePagination(CallbackData, prefix='ex_pag'):
    """
    CallbackData для пагинации выбора упражнения
    """

    action: PaginationAction
    page: int
    exercise_id: int



def get_ikb_select_exercise_fab(
    exercise_data: List[Exercise],
    page: int = 0,
    page_size: int = 5,
    has_next_button: bool = False,
    has_acept_addition_button: bool = False,
    selected_exercise_id: int | None = None
) -> InlineKeyboardMarkup:
    """
    Фабрика для создания инлайн клавиатуры для выбора упражнения
    """
    builder = InlineKeyboardBuilder()
    
    if has_acept_addition_button:
        builder.row(InlineKeyboardButton(text="✅ Добавить ✅", callback_data="acept_addition"))
    
    for exercise in exercise_data[page * page_size:(page + 1) * page_size]:
        select_flag = " ⭐" if exercise.id == selected_exercise_id else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{exercise.name}{select_flag}",
                callback_data=TrainingExercisePagination(
                    action=PaginationAction.SET,
                    page=page,
                    exercise_id=exercise.id,
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
        *[InlineKeyboardButton(text=f"⬅️ Меню {'' if has_next_button else '⬅️'}", callback_data="to_menu")] + ([
            InlineKeyboardButton(text="Вес ➡️", callback_data="to_weight")
        ] if has_next_button else [])
    )
    return builder.as_markup()
