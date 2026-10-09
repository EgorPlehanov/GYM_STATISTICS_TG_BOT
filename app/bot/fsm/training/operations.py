"""Операции изменения типизированного FSM draft тренировки."""

from datetime import date, datetime
from decimal import Decimal

from .draft import TrainingDraft, TrainingDraftExercise, TrainingDraftSet


def add_exercise_to_draft(
    draft: TrainingDraft,
    exercise_id: int,
    exercise_name: str,
) -> None:
    """Добавляет упражнение в draft, если его еще нет.

    Args:
        draft: текущий FSM draft тренировки.
        exercise_id: внутренний id упражнения.
        exercise_name: название упражнения для отображения.

    Returns:
        None. Draft изменяется на месте.
    """
    if _find_exercise(draft, exercise_id) is not None:
        return

    draft.training.exercises.append(
        TrainingDraftExercise(
            exercise_id=exercise_id,
            exercise_name=exercise_name,
        )
    )


def add_set_to_draft(
    draft: TrainingDraft,
    exercise_id: int,
    *,
    weight: Decimal,
    repetitions: int,
    execution_time: date | datetime | str | None = None,
) -> None:
    """Добавляет подход к упражнению в draft.

    Args:
        draft: текущий FSM draft тренировки.
        exercise_id: внутренний id упражнения.
        weight: вес в килограммах.
        repetitions: количество повторений.
        execution_time: время выполнения подхода. При передаче datetime/date
            нормализуется в ISO-строку.

    Returns:
        None. Draft изменяется на месте.

    Raises:
        KeyError: если упражнение отсутствует в draft.
    """
    exercise = _get_exercise(draft, exercise_id)
    exercise.sets.append(
        TrainingDraftSet(
            set_id=None,
            set_number=_get_next_global_set_number(draft),
            weight=weight,
            repetitions=repetitions,
            execution_time=_normalize_execution_time(execution_time),
        )
    )


def update_set_in_draft(
    draft: TrainingDraft,
    exercise_id: int,
    set_id: int,
    *,
    new_weight: Decimal | None = None,
    new_repetitions: int | None = None,
    new_time: date | datetime | str | None = None,
) -> bool:
    """Обновляет подход в draft по локальному номеру внутри упражнения.

    Args:
        draft: текущий FSM draft тренировки.
        exercise_id: внутренний id упражнения.
        set_id: локальный номер подхода внутри упражнения.
        new_weight: новый вес, если его нужно изменить.
        new_repetitions: новое количество повторений, если его нужно изменить.
        new_time: новое время выполнения, если его нужно изменить.

    Returns:
        True, если подход был изменен. False, если данных для изменения нет или
        упражнение/подход не найдены.
    """
    set_data = _get_set_by_local_id(draft, exercise_id, set_id)
    if set_data is None:
        return False

    updated = False
    if new_weight is not None and new_weight != set_data.weight:
        set_data.weight = new_weight
        updated = True
    if new_repetitions is not None and new_repetitions != set_data.repetitions:
        set_data.repetitions = new_repetitions
        updated = True
    if new_time is not None:
        normalized_time = _normalize_execution_time(new_time)
        if normalized_time != set_data.execution_time:
            set_data.execution_time = normalized_time
            updated = True

    return updated


def delete_set_from_draft(
    draft: TrainingDraft,
    exercise_id: int,
    set_id: int,
) -> None:
    """Удаляет подход из draft по локальному номеру внутри упражнения.

    Args:
        draft: текущий FSM draft тренировки.
        exercise_id: внутренний id упражнения.
        set_id: локальный номер подхода внутри упражнения.

    Returns:
        None. Если после удаления у упражнения не осталось подходов, упражнение
        тоже удаляется из draft.

    Raises:
        KeyError: если упражнение или подход не найдены.
    """
    exercise = _get_exercise(draft, exercise_id)
    local_index = _local_set_index(set_id)
    if local_index >= len(exercise.sets):
        raise KeyError(f"Подход {set_id} не найден")

    del exercise.sets[local_index]
    if not exercise.sets:
        delete_exercise_from_draft(draft, exercise_id)
    else:
        recalculate_draft_set_numbers(draft)


def delete_all_exercise_sets_from_draft(
    draft: TrainingDraft,
    exercise_id: int,
) -> None:
    """Удаляет упражнение со всеми подходами из draft.

    Args:
        draft: текущий FSM draft тренировки.
        exercise_id: внутренний id упражнения.

    Returns:
        None. Draft изменяется на месте.

    Raises:
        KeyError: если упражнение не найдено.
    """
    delete_exercise_from_draft(draft, exercise_id)


def delete_exercise_from_draft(
    draft: TrainingDraft,
    exercise_id: int,
) -> None:
    """Удаляет упражнение из draft.

    Args:
        draft: текущий FSM draft тренировки.
        exercise_id: внутренний id упражнения.

    Returns:
        None. Draft изменяется на месте.

    Raises:
        KeyError: если упражнение не найдено.
    """
    exercise = _get_exercise(draft, exercise_id)
    draft.training.exercises.remove(exercise)
    recalculate_draft_set_numbers(draft)


def delete_all_exercises_from_draft(draft: TrainingDraft) -> None:
    """Удаляет все упражнения из draft.

    Args:
        draft: текущий FSM draft тренировки.

    Returns:
        None. Draft изменяется на месте.
    """
    draft.training.exercises.clear()
    recalculate_draft_set_numbers(draft)


def recalculate_draft_set_numbers(draft: TrainingDraft) -> None:
    """Пересчитывает глобальные номера подходов в порядке хранения draft.

    Args:
        draft: текущий FSM draft тренировки.

    Returns:
        None. Поле `set_number` всех подходов обновляется на месте.
    """
    counter = 0
    for exercise in draft.training.exercises:
        for set_data in exercise.sets:
            counter += 1
            set_data.set_number = counter


def has_draft_exercises(draft: TrainingDraft) -> bool:
    """Проверяет, есть ли упражнения в draft.

    Args:
        draft: текущий FSM draft тренировки.

    Returns:
        True, если в тренировке есть хотя бы одно упражнение.
    """
    return bool(draft.training.exercises)


def get_draft_exercise(
    draft: TrainingDraft,
    exercise_id: int,
) -> TrainingDraftExercise:
    """Возвращает упражнение из draft по id.

    Args:
        draft: текущий FSM draft тренировки.
        exercise_id: внутренний id упражнения.

    Returns:
        Найденное упражнение.

    Raises:
        KeyError: если упражнение отсутствует в draft.
    """
    return _get_exercise(draft, exercise_id)


def get_draft_set_by_local_id(
    draft: TrainingDraft,
    exercise_id: int,
    set_id: int,
) -> TrainingDraftSet:
    """Возвращает подход по локальному номеру внутри упражнения.

    Args:
        draft: текущий FSM draft тренировки.
        exercise_id: внутренний id упражнения.
        set_id: локальный номер подхода внутри упражнения.

    Returns:
        Найденный подход.

    Raises:
        KeyError: если упражнение или подход отсутствуют в draft.
    """
    set_data = _get_set_by_local_id(draft, exercise_id, set_id)
    if set_data is None:
        raise KeyError(f"Подход {set_id} не найден")
    return set_data


def _find_exercise(
    draft: TrainingDraft,
    exercise_id: int,
) -> TrainingDraftExercise | None:
    """Возвращает упражнение по id или None."""
    return next(
        (
            exercise
            for exercise in draft.training.exercises
            if exercise.exercise_id == exercise_id
        ),
        None,
    )


def _get_exercise(
    draft: TrainingDraft,
    exercise_id: int,
) -> TrainingDraftExercise:
    """Возвращает упражнение по id или выбрасывает KeyError."""
    exercise = _find_exercise(draft, exercise_id)
    if exercise is None:
        raise KeyError(f"Упражнение {exercise_id} не найдено")
    return exercise


def _get_set_by_local_id(
    draft: TrainingDraft,
    exercise_id: int,
    set_id: int,
) -> TrainingDraftSet | None:
    """Возвращает подход по локальному номеру внутри упражнения."""
    try:
        exercise = _get_exercise(draft, exercise_id)
    except KeyError:
        return None

    local_index = _local_set_index(set_id)
    if local_index < 0 or local_index >= len(exercise.sets):
        return None
    return exercise.sets[local_index]


def _local_set_index(set_id: int) -> int:
    """Преобразует legacy local set id в индекс списка."""
    return set_id - 1


def _get_next_global_set_number(draft: TrainingDraft) -> int:
    """Возвращает следующий глобальный номер подхода."""
    return sum(len(exercise.sets) for exercise in draft.training.exercises) + 1


def _normalize_execution_time(value: date | datetime | str | None) -> str | None:
    """Нормализует время выполнения подхода в ISO-строку."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value
