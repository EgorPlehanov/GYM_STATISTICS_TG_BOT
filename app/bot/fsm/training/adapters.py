"""Адаптеры между legacy FSM-структурой и типизированным draft тренировки."""

from datetime import date, datetime
from typing import Any

from .draft import (
    TrainingDraft,
    TrainingDraftData,
    TrainingDraftExercise,
    TrainingDraftSet,
)


def legacy_exercise_data_to_draft(exercise_data: dict[str, Any]) -> TrainingDraft:
    """Преобразует старый `exercise_data` в типизированный FSM draft.

    Args:
        exercise_data: legacy-структура тренировки из текущего Telegram FSM/API
            контракта. Содержит `date`, `comment`, `global_set_counter` и словарь
            `exercises` с вложенными словарями `sets`.

    Returns:
        Типизированный `TrainingDraft` с JSON-friendly датами и временем.
    """
    return TrainingDraft(
        training=TrainingDraftData(
            training_id=exercise_data.get("id"),
            training_date=_normalize_date(exercise_data["date"]),
            comment=exercise_data.get("comment"),
            exercises=[
                TrainingDraftExercise(
                    exercise_id=_to_int(exercise_id),
                    exercise_name=exercise["exercise_name"],
                    sets=[
                        TrainingDraftSet(
                            set_id=set_data.get("id"),
                            set_number=set_data["set_number"],
                            weight=set_data["weight"],
                            repetitions=set_data["repetitions"],
                            execution_time=_normalize_datetime_or_none(
                                set_data.get("time")
                            ),
                        )
                        for _, set_data in _iter_sorted_sets(exercise.get("sets", {}))
                    ],
                )
                for exercise_id, exercise in _iter_legacy_exercises(
                    exercise_data.get("exercises", {})
                )
            ],
        )
    )


def draft_to_legacy_exercise_data(
    draft: TrainingDraft,
    *,
    user_id: int | None = None,
) -> dict[str, Any]:
    """Преобразует типизированный FSM draft в старый `exercise_data`.

    Args:
        draft: типизированный черновик тренировки.
        user_id: Telegram user id для старого save-контракта. Значение передается
            отдельно, чтобы не хранить пользовательский id внутри целевого FSM draft.

    Returns:
        Legacy-структура с числовыми ключами упражнений/подходов и полем `time`
        внутри подходов. Этот формат пока ожидают текущие handlers и internal API.
    """
    exercises: dict[int, dict[str, Any]] = {}
    global_set_counter = 0

    for exercise in draft.training.exercises:
        legacy_sets = {}
        for local_set_number, set_data in enumerate(exercise.sets, start=1):
            legacy_sets[local_set_number] = {
                "id": set_data.set_id,
                "set_number": set_data.set_number,
                "weight": set_data.weight,
                "repetitions": set_data.repetitions,
                "time": _parse_datetime_or_none(set_data.execution_time),
            }
            global_set_counter = max(global_set_counter, set_data.set_number)

        exercises[exercise.exercise_id] = {
            "exercise_name": exercise.exercise_name,
            "local_set_counter": len(legacy_sets),
            "sets": legacy_sets,
        }

    return {
        "id": draft.training.training_id,
        "user_id": user_id,
        "date": _parse_date(draft.training.training_date),
        "comment": draft.training.comment,
        "global_set_counter": global_set_counter,
        "exercises": exercises,
    }


def draft_to_legacy_exercises_data(draft: TrainingDraft) -> dict[int, dict[str, Any]]:
    """Возвращает legacy-словарь упражнений из draft.

    Args:
        draft: типизированный черновик тренировки.

    Returns:
        Словарь `exercises` из старого FSM-формата. Нужен как переходный адаптер
        для клавиатур, которые пока ожидают dict с числовыми ключами.
    """
    return draft_to_legacy_exercise_data(draft)["exercises"]


def draft_to_legacy_exercise_sets_data(
    draft: TrainingDraft,
    exercise_id: int,
) -> dict[int, dict[str, Any]]:
    """Возвращает legacy-словарь подходов упражнения из draft.

    Args:
        draft: типизированный черновик тренировки.
        exercise_id: внутренний id упражнения.

    Returns:
        Словарь `sets` из старого FSM-формата. Нужен как переходный адаптер
        для клавиатур выбора подхода.

    Raises:
        KeyError: если упражнение отсутствует в draft.
    """
    return draft_to_legacy_exercises_data(draft)[exercise_id]["sets"]


def _iter_legacy_exercises(
    exercises: dict[str | int, dict[str, Any]],
) -> list[tuple[str | int, dict[str, Any]]]:
    """Возвращает legacy-упражнения в предсказуемом порядке ключей."""
    return sorted(exercises.items(), key=lambda item: _to_int(item[0]))


def _iter_sorted_sets(
    sets: dict[str | int, dict[str, Any]],
) -> list[tuple[str | int, dict[str, Any]]]:
    """Возвращает legacy-подходы в порядке локального номера подхода."""
    return sorted(sets.items(), key=lambda item: _to_int(item[0]))


def _normalize_date(value: date | datetime | str) -> str:
    """Возвращает дату тренировки в формате YYYY-MM-DD."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _normalize_datetime_or_none(value: datetime | str | None) -> str | None:
    """Возвращает время подхода в ISO-формате или None."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _parse_date(value: date | datetime | str) -> date:
    """Возвращает `date` для старого FSM/API-контракта."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _parse_datetime_or_none(value: datetime | str | None) -> datetime | None:
    """Возвращает `datetime` для старого FSM/API-контракта."""
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _to_int(value: str | int) -> int:
    """Приводит legacy-ключ словаря к `int`."""
    return int(value)
