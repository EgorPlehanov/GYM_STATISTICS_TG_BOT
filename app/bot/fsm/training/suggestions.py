"""Подсказки для FSM-сценария тренировки."""

from .draft import TrainingDraft, TrainingDraftExercise, TrainingSetModeSuggestion


def get_current_exercise_id_from_draft(
    draft: TrainingDraft,
) -> int | None:
    """Возвращает id текущего упражнения из типизированного FSM draft.

    Args:
        draft: текущий draft сценария тренировки.

    Returns:
        Id упражнения для редактирования, добавления или повтора подхода.
    """
    if draft.edit.exercise_id is not None:
        return draft.edit.exercise_id
    if draft.selection.exercise_id is not None:
        return draft.selection.exercise_id
    return draft.ui.current_exercise_id


def get_current_set_id_from_draft(
    draft: TrainingDraft,
    current_exercise_id: int | None = None,
) -> int | None:
    """Возвращает локальный номер текущего подхода из типизированного FSM draft.

    Args:
        draft: текущий draft сценария тренировки.
        current_exercise_id: id упражнения, для которого нужно определить подход.

    Returns:
        Локальный номер редактируемого или следующего добавляемого подхода.
    """
    if draft.edit.set_id is not None:
        return draft.edit.set_id

    exercise = _find_draft_exercise(draft, current_exercise_id)
    if exercise is None:
        return 1
    return len(exercise.sets) + 1


def get_weight_repetitions_modes_values_from_draft(
    draft: TrainingDraft,
    *,
    is_weight: bool = False,
    is_repetitions: bool = False,
) -> str | tuple[str, str] | None:
    """Возвращает подсказки веса и повторений из типизированного FSM draft.

    Args:
        draft: текущий draft сценария тренировки.
        is_weight: вернуть подсказку веса.
        is_repetitions: вернуть подсказку количества повторений.

    Returns:
        Строка с подсказкой веса/повторений, кортеж из двух строк или пустое
        значение, если для текущего упражнения нет рассчитанной моды.
    """
    exercise_id = get_current_exercise_id_from_draft(draft)
    if exercise_id is None:
        return _empty_suggestion(is_weight=is_weight, is_repetitions=is_repetitions)

    exercise_mode = draft.suggestions.weight_repetitions_modes.get(exercise_id)
    if exercise_mode is None:
        return _empty_suggestion(is_weight=is_weight, is_repetitions=is_repetitions)

    max_exercise_order = exercise_mode.max_exercise_order
    sets_modes = exercise_mode.sets_modes
    set_id = get_current_set_id_from_draft(draft, exercise_id)

    if set_id is None or max_exercise_order is None or not sets_modes:
        return _empty_suggestion(is_weight=is_weight, is_repetitions=is_repetitions)

    if set_id > max_exercise_order:
        set_modes = sets_modes.get(max_exercise_order)
    else:
        set_modes = sets_modes.get(set_id)

    return _format_weight_repetitions_modes(
        set_modes,
        is_weight=is_weight,
        is_repetitions=is_repetitions,
    )


def _find_draft_exercise(
    draft: TrainingDraft,
    exercise_id: int | None,
) -> TrainingDraftExercise | None:
    """Возвращает упражнение из draft по id."""
    if exercise_id is None:
        return None
    return next(
        (
            exercise
            for exercise in draft.training.exercises
            if exercise.exercise_id == exercise_id
        ),
        None,
    )


def _format_weight_repetitions_modes(
    set_modes: TrainingSetModeSuggestion | None,
    *,
    is_weight: bool,
    is_repetitions: bool,
) -> str | tuple[str, str] | None:
    """Форматирует рассчитанные моды в контракт inline search."""
    if set_modes is None:
        return _empty_suggestion(is_weight=is_weight, is_repetitions=is_repetitions)

    weight = set_modes.weight_mode
    repetitions = set_modes.repetitions_mode
    if is_weight and is_repetitions:
        return str(weight), str(repetitions)
    if is_weight:
        return str(weight)
    if is_repetitions:
        return str(repetitions)
    return None


def _empty_suggestion(*, is_weight: bool, is_repetitions: bool) -> str | tuple[str, str]:
    """Возвращает пустую подсказку в старом формате функции."""
    if is_weight and is_repetitions:
        return "", ""
    return ""

