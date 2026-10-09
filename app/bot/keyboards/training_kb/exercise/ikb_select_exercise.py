import math
from collections.abc import Mapping, Sequence
from typing import Protocol

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ...keyboards_types import PaginationAction


class ExerciseButtonData(Protocol):
    """Минимальные данные упражнения, необходимые для кнопки выбора."""

    id: int
    name: str


ExerciseButtonItem = ExerciseButtonData | Mapping[str, object]



class TrainingExercisePagination(CallbackData, prefix='ex_pag'):
    """
    CallbackData для пагинации выбора упражнения
    """

    action: PaginationAction
    page: int
    exercise_id: int



def get_ikb_select_exercise_fab(
    exercise_data: Sequence[ExerciseButtonItem],
    page: int = 0,
    page_size: int = 5,
    selected_exercise_id: int | None = None,
    back_button_callback_data: str = "to_menu",
    back_button_text: str = "← Меню",
) -> InlineKeyboardMarkup:
    """
    Фабрика для создания инлайн клавиатуры для выбора упражнения
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text = "🔎 Найти в поиске 🔎",
        switch_inline_query_current_chat = ""
    ))
    
    for exercise in exercise_data[page * page_size:(page + 1) * page_size]:
        exercise_id = _get_exercise_id(exercise)
        exercise_name = _get_exercise_name(exercise)
        select_flag = " ⭐" if exercise_id == selected_exercise_id else ""
        builder.row(
            InlineKeyboardButton(
                text=f"{exercise_name}{select_flag}",
                callback_data=TrainingExercisePagination(
                    action=PaginationAction.SET,
                    page=page,
                    exercise_id=exercise_id,
                ).pack()
            )
        )

    builder.row(*([
        InlineKeyboardButton(
            text="←",
            callback_data=TrainingExercisePagination(
                action=PaginationAction.PREV,
                page=page,
                exercise_id=-1,
            ).pack()
        )
    ] if page > 0 else []) + ([
        InlineKeyboardButton(
            text="→",
            callback_data=TrainingExercisePagination(
                action=PaginationAction.NEXT,
                page=page,
                exercise_id=-1,
            ).pack()
        )
    ] if page < math.ceil(len(exercise_data) / page_size) - 1 else []))

    builder.row(
        InlineKeyboardButton(
            text=back_button_text,
            callback_data=back_button_callback_data,
        )
    )

    return builder.as_markup()


def _get_exercise_id(exercise: ExerciseButtonItem) -> int:
    """Возвращает id упражнения из DTO или JSON-friendly dict."""
    if isinstance(exercise, Mapping):
        return int(exercise["id"])
    return exercise.id


def _get_exercise_name(exercise: ExerciseButtonItem) -> str:
    """Возвращает название упражнения из DTO или JSON-friendly dict."""
    if isinstance(exercise, Mapping):
        return str(exercise["name"])
    return exercise.name


