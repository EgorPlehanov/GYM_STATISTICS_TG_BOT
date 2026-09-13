
from aiogram.fsm.context import FSMContext

from .draft import TrainingDraft, TrainingDraftSet, get_training_draft
from .states import TrainingMode


async def check_accept_addition(state: FSMContext) -> bool:
    """Проверяет, можно ли подтвердить добавление или изменение подхода."""
    return check_accept_addition_for_draft(await get_training_draft(state))


def check_accept_addition_for_draft(draft: TrainingDraft) -> bool:
    """Проверяет возможность подтверждения по типизированному FSM draft.

    Args:
        draft: текущий draft сценария тренировки.

    Returns:
        True, если текущий ввод достаточно заполнен и его можно применить.
    """
    is_exercise = draft.selection.exercise_id is not None
    is_weight = draft.selection.weight is not None
    is_repetitions = draft.selection.repetitions is not None

    match _get_training_mode(draft.selection.mode):
        case TrainingMode.ADD_EXERCISE:
            return is_exercise and is_weight and is_repetitions
        case TrainingMode.ADD_SET:
            return is_weight and is_repetitions
        case TrainingMode.EDIT_SET:
            set_data = _get_edit_set(draft)
            if set_data is None:
                return False

            return (
                (is_weight and is_repetitions)
                and (
                    set_data.weight != draft.selection.weight
                    or set_data.repetitions != draft.selection.repetitions
                )
            )
        case _:
            return False


def _get_training_mode(value: str | TrainingMode | None) -> TrainingMode | None:
    """Возвращает `TrainingMode` из строки draft или старого enum."""
    if value is None or isinstance(value, TrainingMode):
        return value
    try:
        return TrainingMode(value)
    except ValueError:
        return None


def _get_edit_set(draft: TrainingDraft) -> TrainingDraftSet | None:
    """Возвращает редактируемый подход из draft по legacy local set id."""
    if draft.edit.exercise_id is None or draft.edit.set_id is None:
        return None

    exercise = next(
        (
            exercise
            for exercise in draft.training.exercises
            if exercise.exercise_id == draft.edit.exercise_id
        ),
        None,
    )
    if exercise is None:
        return None

    local_set_index = draft.edit.set_id - 1
    if local_set_index < 0 or local_set_index >= len(exercise.sets):
        return None
    return exercise.sets[local_set_index]

