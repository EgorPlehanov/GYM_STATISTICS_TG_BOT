"""Клавиатуры сценария добавления и редактирования тренировки."""

from .date import (
    WEEKDAYS,
    DialogCalendar,
    DialogCalendarAction,
    DialogCalendarCallback,
    SimpleCalendar,
    SimpleCalendarAction,
    SimpleCalendarCallback,
    get_ikb_changed_date,
    get_ikb_select_date,
)
from .edit import (
    EditTrainingExercisePagination,
    EditTrainingSetPagination,
    get_ikb_edit_menu,
    get_ikb_edit_select_exercise_fab,
    get_ikb_edit_select_set_fab,
    ikb_edit_accept_delete,
)
from .exercise import (
    TrainingExercisePagination,
    get_ikb_select_exercise_fab,
)
from .ikb_finish_add_comment import get_ikb_finish_add_comment
from .ikb_training_menu import get_ikb_training_menu
from .set_input import (
    get_ikb_accept_addition,
    get_ikb_open_inline_search,
)

__all__ = [
    "DialogCalendar",
    "DialogCalendarAction",
    "DialogCalendarCallback",
    "EditTrainingExercisePagination",
    "EditTrainingSetPagination",
    "SimpleCalendar",
    "SimpleCalendarAction",
    "SimpleCalendarCallback",
    "TrainingExercisePagination",
    "WEEKDAYS",
    "get_ikb_accept_addition",
    "get_ikb_changed_date",
    "get_ikb_edit_menu",
    "get_ikb_edit_select_exercise_fab",
    "get_ikb_edit_select_set_fab",
    "get_ikb_finish_add_comment",
    "get_ikb_open_inline_search",
    "get_ikb_select_date",
    "get_ikb_select_exercise_fab",
    "get_ikb_training_menu",
    "ikb_edit_accept_delete",
]
