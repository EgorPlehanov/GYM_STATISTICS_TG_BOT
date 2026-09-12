from app.bot.fsm.training import TrainingStates

from .date import router as select_date_router
from .edit import (
    edit_menu_router,
    edit_select_exercise_router,
    edit_select_set_router,
)
from .exercise import router as select_exercise_router
from .finish import router as finish_add_comment_router
from .set_input import (
    accept_router,
    select_repetitions_router,
    select_sets_count_router,
    select_weight_router,
)

__all__ = [
    "TrainingStates",
    "accept_router",
    "edit_menu_router",
    "edit_select_exercise_router",
    "edit_select_set_router",
    "finish_add_comment_router",
    "select_date_router",
    "select_exercise_router",
    "select_repetitions_router",
    "select_sets_count_router",
    "select_weight_router",
]


