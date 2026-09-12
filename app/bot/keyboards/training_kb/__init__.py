"""Клавиатуры сценария добавления и редактирования тренировки."""

from .date import (
    DialogCalendar,
    DialogCalendarAction,
    DialogCalendarCallback,
    SimpleCalendar,
    SimpleCalendarAction,
    SimpleCalendarCallback,
    WEEKDAYS,
    get_ikb_select_date,
)

from .ikb_select_exercise import (
    get_ikb_select_exercise_fab,
    TrainingExercisePagination,
)
from .ikb_open_inline_search import get_ikb_open_inline_search

from .ikb_training_menu import get_ikb_training_menu

from .ikb_acept_addition import get_ikb_acept_addition
from .ikb_finish_add_comment import get_ikb_finish_add_comment

from .ikb_edit_menu import get_ikb_edit_menu
from .ikb_edit_select_exercise import (
    get_ikb_edit_select_exercise_fab,
    EditTrainingExercisePagination,
)
from .ikb_edit_select_set import (
    get_ikb_edit_select_set_fab,
    EditTrainingSetPagination,
)
from .ikb_edit_acept_delete import ikb_edit_acept_delete
from .ikb_changed_date import get_ikb_changed_date

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
    "get_ikb_acept_addition",
    "get_ikb_changed_date",
    "get_ikb_edit_menu",
    "get_ikb_edit_select_exercise_fab",
    "get_ikb_edit_select_set_fab",
    "get_ikb_finish_add_comment",
    "get_ikb_open_inline_search",
    "get_ikb_select_date",
    "get_ikb_select_exercise_fab",
    "get_ikb_training_menu",
    "ikb_edit_acept_delete",
]
