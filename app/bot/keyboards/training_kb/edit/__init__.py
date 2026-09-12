"""Клавиатуры редактирования тренировки."""

from .ikb_edit_accept_delete import ikb_edit_accept_delete
from .ikb_edit_menu import get_ikb_edit_menu
from .ikb_edit_select_exercise import (
    EditTrainingExercisePagination,
    get_ikb_edit_select_exercise_fab,
)
from .ikb_edit_select_set import EditTrainingSetPagination, get_ikb_edit_select_set_fab

__all__ = [
    "EditTrainingExercisePagination",
    "EditTrainingSetPagination",
    "get_ikb_edit_menu",
    "get_ikb_edit_select_exercise_fab",
    "get_ikb_edit_select_set_fab",
    "ikb_edit_accept_delete",
]
