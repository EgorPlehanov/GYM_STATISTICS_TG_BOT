import math

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.fsm.training.draft import TrainingDraftExercise

from ...keyboards_types import PaginationAction



class EditTrainingExercisePagination(CallbackData, prefix='ed_ex_pag'):
    """
    CallbackData для пагинации выбора упражнения
    """
    
    action: PaginationAction
    page: int
    exercise_id: int



def get_ikb_edit_select_exercise_fab(
    exercises: list[TrainingDraftExercise],
    page: int = 0,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    """Фабрика inline-клавиатуры выбора упражнения из текущего draft.

    Args:
        exercises: упражнения текущей тренировки в порядке отображения.
        page: текущая страница пагинации.
        page_size: количество упражнений на странице.

    Returns:
        Inline-клавиатура выбора упражнения для редактирования.
    """
    builder = InlineKeyboardBuilder()
    
    for i in range(page * page_size, (page + 1) * page_size):
        if i >= len(exercises):
            break
        exercise = exercises[i]
        builder.row(
            InlineKeyboardButton(
                text=exercise.exercise_name,
                callback_data=EditTrainingExercisePagination(
                    action=PaginationAction.SET,
                    page=page,
                    exercise_id=exercise.exercise_id,
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
    ] if page < math.ceil(len(exercises) / page_size) - 1 else []))
    builder.row(InlineKeyboardButton(text="⬅️ Назад ⬅️", callback_data="to_edit_menu"))
    builder.row(InlineKeyboardButton(text="🗑️ Удалить все 🗑️", callback_data="delete_all_exercises"))
    return builder.as_markup()


