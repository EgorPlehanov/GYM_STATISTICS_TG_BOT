from .training_types import (
    TrainingMode,
    TrainingStates,
    exercise_button_by_mode,
    weight_back_button_by_mode,
    acept_button_by_mode
)
from .training_select_date import router as select_date_router
from .training_select_exercise import router as select_exercise_router
from .training_select_weight import router as select_weight_router
from .training_select_repetitions import router as select_repetitions_router
from .training_select_sets_count import router as select_sets_count_router
from .training_acept import router as acept_router
from .training_edit_menu import router as edit_menu_router
from .training_edit_select_exercise import router as edit_select_exercise_router
from .training_edit_select_set import router as edit_select_set_router
from .training_finish_add_comment import router as finish_add_comment_router
