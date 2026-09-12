"""Обработчики редактирования тренировки."""

from .exercise import router as edit_select_exercise_router
from .menu import router as edit_menu_router
from .set import router as edit_select_set_router

__all__ = [
    "edit_menu_router",
    "edit_select_exercise_router",
    "edit_select_set_router",
]
