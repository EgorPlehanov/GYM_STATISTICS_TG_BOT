"""Обработчики ввода данных подхода в сценарии тренировки."""

from .accept import router as accept_router
from .form import router as add_set_form_router

__all__ = [
    "accept_router",
    "add_set_form_router",
]
