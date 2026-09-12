"""Обработчики ввода данных подхода в сценарии тренировки."""

from .accept import router as accept_router
from .repetitions import router as select_repetitions_router
from .sets_count import router as select_sets_count_router
from .weight import router as select_weight_router

__all__ = [
    "accept_router",
    "select_repetitions_router",
    "select_sets_count_router",
    "select_weight_router",
]
