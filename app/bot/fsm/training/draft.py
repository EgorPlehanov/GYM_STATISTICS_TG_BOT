"""Операции над текущим FSM-черновиком тренировки."""

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(slots=True)
class TrainingDraftSet:
    """JSON-friendly данные подхода внутри FSM draft.

    Attributes:
        set_id: внутренний id подхода, если подход уже сохранен в backend.
        set_number: порядковый номер подхода в тренировке.
        weight: вес в килограммах.
        repetitions: количество повторений.
        execution_time: время выполнения подхода в ISO-формате или None.
    """

    set_id: int | None
    set_number: int
    weight: float
    repetitions: int
    execution_time: str | None = None


@dataclass(slots=True)
class TrainingDraftExercise:
    """JSON-friendly данные упражнения внутри FSM draft.

    Attributes:
        exercise_id: внутренний id упражнения.
        exercise_name: название упражнения для отображения в Telegram.
        sets: список подходов упражнения.
    """

    exercise_id: int
    exercise_name: str
    sets: list[TrainingDraftSet] = field(default_factory=list)


@dataclass(slots=True)
class TrainingDraftData:
    """Основной черновик тренировки, который пользователь собирает в Telegram.

    Attributes:
        training_id: внутренний id тренировки, если редактируется существующая запись.
        training_date: дата тренировки. При сериализации нормализуется в YYYY-MM-DD.
        comment: комментарий к тренировке.
        exercises: упражнения и подходы текущей тренировки.
    """

    training_id: int | None
    training_date: date | datetime | str
    comment: str | None = None
    exercises: list[TrainingDraftExercise] = field(default_factory=list)


@dataclass(slots=True)
class TrainingSelection:
    """Временные значения текущего ввода в сценарии тренировки.

    Attributes:
        mode: режим добавления или редактирования.
        exercise_id: id упражнения текущего ввода.
        exercise_name: имя упражнения текущего ввода.
        weight: выбранный вес.
        repetitions: выбранное количество повторений.
        sets_count: выбранное количество подходов.
    """

    mode: str | None = None
    exercise_id: int | None = None
    exercise_name: str | None = None
    weight: float | None = None
    repetitions: int | None = None
    sets_count: int | None = None


@dataclass(slots=True)
class TrainingEditContext:
    """Контекст выбранной сущности в режиме редактирования.

    Attributes:
        exercise_id: id редактируемого упражнения.
        exercise_name: имя редактируемого упражнения.
        set_id: id редактируемого подхода внутри упражнения.
        set_number: номер редактируемого подхода в тренировке.
    """

    exercise_id: int | None = None
    exercise_name: str | None = None
    set_id: int | None = None
    set_number: int | None = None


@dataclass(slots=True)
class TrainingUiContext:
    """Telegram UI-контекст сценария тренировки.

    Attributes:
        message_id: id основного Telegram-сообщения, которое редактирует бот.
        state_before_delete: состояние FSM до экрана подтверждения удаления.
        reply_markup_before_delete: JSON-compatible представление клавиатуры до удаления.
    """

    message_id: int | None = None
    state_before_delete: str | None = None
    reply_markup_before_delete: dict[str, Any] | None = None


@dataclass(slots=True)
class TrainingSuggestions:
    """Подсказки, загруженные из backend для Telegram-сценария.

    Attributes:
        most_frequent_exercises: частые упражнения пользователя.
        weight_repetitions_modes: подсказки веса и повторений.
        training_dates: даты существующих тренировок в формате YYYY-MM-DD.
    """

    most_frequent_exercises: list[dict[str, Any]] = field(default_factory=list)
    weight_repetitions_modes: list[dict[str, Any]] = field(default_factory=list)
    training_dates: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TrainingDraft:
    """Полный JSON-friendly FSM draft сценария тренировки.

    Attributes:
        training: основной черновик тренировки.
        selection: временные значения текущего ввода.
        edit: контекст редактирования.
        ui: Telegram UI-контекст.
        suggestions: подсказки для сценария.
    """

    training: TrainingDraftData
    selection: TrainingSelection = field(default_factory=TrainingSelection)
    edit: TrainingEditContext = field(default_factory=TrainingEditContext)
    ui: TrainingUiContext = field(default_factory=TrainingUiContext)
    suggestions: TrainingSuggestions = field(default_factory=TrainingSuggestions)


def draft_to_json(draft: TrainingDraft) -> dict[str, Any]:
    """Преобразует FSM draft в JSON-compatible словарь.

    Args:
        draft: типизированный черновик тренировки.

    Returns:
        Словарь, который можно сохранить в Redis FSM storage или сериализовать в JSON.
    """
    return _normalize_json_value(asdict(draft))


def draft_from_json(data: dict[str, Any]) -> TrainingDraft:
    """Восстанавливает типизированный FSM draft из JSON-compatible словаря.

    Args:
        data: словарь, полученный из FSM storage или JSON.

    Returns:
        Типизированный черновик тренировки.
    """
    training_data = data["training"]
    return TrainingDraft(
        training=TrainingDraftData(
            training_id=training_data.get("training_id"),
            training_date=_normalize_date(training_data["training_date"]),
            comment=training_data.get("comment"),
            exercises=[
                TrainingDraftExercise(
                    exercise_id=exercise["exercise_id"],
                    exercise_name=exercise["exercise_name"],
                    sets=[
                        TrainingDraftSet(
                            set_id=set_data.get("set_id"),
                            set_number=set_data["set_number"],
                            weight=set_data["weight"],
                            repetitions=set_data["repetitions"],
                            execution_time=_normalize_datetime_or_none(
                                set_data.get("execution_time")
                            ),
                        )
                        for set_data in exercise.get("sets", [])
                    ],
                )
                for exercise in training_data.get("exercises", [])
            ],
        ),
        selection=TrainingSelection(**data.get("selection", {})),
        edit=TrainingEditContext(**data.get("edit", {})),
        ui=TrainingUiContext(**data.get("ui", {})),
        suggestions=TrainingSuggestions(**data.get("suggestions", {})),
    )


def _normalize_json_value(value: Any) -> Any:
    """Рекурсивно приводит значение к JSON-friendly формату."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _normalize_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]
    return value


def _normalize_date(value: date | datetime | str) -> str:
    """Возвращает дату в формате YYYY-MM-DD."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _normalize_datetime_or_none(value: datetime | str | None) -> str | None:
    """Возвращает время в ISO-формате или None."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def add_exercise(
    exercise_data: dict[str, Any], exercise_id: str, exercise_name: str
) -> None:
    """Добавляет упражнение к черновику тренировки."""
    if exercise_id in exercise_data["exercises"]:
        return
    exercise_data["exercises"][exercise_id] = {
        "exercise_name": exercise_name,
        "local_set_counter": 0,
        "sets": {},
    }



def add_set(
    exercise_data: dict[str, Any],
    exercise_id: str,
    weight: int = None,
    repetitions: int = None,
    time: str = None,
) -> None:
    """Добавляет подход к упражнению в черновике тренировки."""
    exercise_data["exercises"][exercise_id]["local_set_counter"] += 1
    exercise_data["global_set_counter"] += 1

    set_number = exercise_data["exercises"][exercise_id]["local_set_counter"]

    exercise_data["exercises"][exercise_id]["sets"][set_number] = {
        "set_number": exercise_data["global_set_counter"],
        "weight": weight,
        "repetitions": repetitions,
        "time": time,
    }




def update_set(
    exercise_data: dict[str, Any],
    exercise_id: int,
    set_id: int,
    new_weight: int = None,
    new_repetitions: int = None,
    new_time: datetime = None,
) -> bool:
    """Обновляет вес, количество повторений или время выполнения подхода."""
    if new_weight is None and new_repetitions is None and new_time is None:
        return False
    
    if (
        exercise_id not in exercise_data["exercises"]
        or set_id not in exercise_data["exercises"][exercise_id]["sets"]
    ):
        return False

    updated_flag = False
    set_data = exercise_data["exercises"][exercise_id]["sets"][set_id]

    if new_weight is not None and new_weight != set_data["weight"]:
        set_data["weight"] = new_weight
        updated_flag = True

    if new_repetitions is not None and new_repetitions != set_data["repetitions"]:
        set_data["repetitions"] = new_repetitions
        updated_flag = True

    if new_time is not None and new_time != set_data["time"]:
        set_data["time"] = new_time
        updated_flag = True

    return updated_flag



def delete_set(
    exercise_data: dict[str, Any],
    exercise_id: str,
    set_number: str
) -> None:
    """Удаляет подход из черновика тренировки."""
    del exercise_data["exercises"][exercise_id]["sets"][set_number]
    # Удаляет упражнение, если нет ни одного подхода
    if not exercise_data['exercises'][exercise_id]['sets']:
        del exercise_data['exercises'][exercise_id]
    update_indexes_exercise_data(exercise_data)



def delete_all_exercise_sets(
    exercise_data: dict[str, Any],
    exercise_id: str,
    is_sets_only: bool = False,
) -> None:
    """Удаляет все подходы упражнения из черновика тренировки."""
    if is_sets_only:
        del exercise_data["exercises"][exercise_id]["sets"]
    else:
        del exercise_data["exercises"][exercise_id]
    update_indexes_exercise_data(exercise_data)



def delete_exercise(
    exercise_data: dict[str, Any], exercise_id: str
) -> None:
    """Удаляет упражнение со всеми подходами из черновика тренировки."""
    del exercise_data["exercises"][exercise_id]
    update_indexes_exercise_data(exercise_data)



def delete_all_exercises(exercise_data: dict[str, Any]) -> None:
    """Удаляет все упражнения из черновика тренировки."""
    exercise_data["exercises"] = {}
    update_indexes_exercise_data(exercise_data)



def update_indexes_exercise_data(
    exercise_data: dict[str, Any],
) -> None:
    """Обновляет локальные и глобальные индексы подходов в черновике."""
    all_sets = []
    for exercise in exercise_data["exercises"].values():
        all_sets.extend(list(exercise["sets"].values()))

        local_set_counter = 0
        sets_keys = list(exercise["sets"].keys())
        for set_idx in sets_keys:
            local_set_counter += 1
            if set_idx != local_set_counter:
                exercise["sets"][local_set_counter] = exercise["sets"].pop(set_idx)

        exercise["local_set_counter"] = local_set_counter
    
    all_sets_sorted = sorted(all_sets, key=lambda x: x["set_number"])
    for idx in range(len(all_sets_sorted)):
        all_sets_sorted[idx]["set_number"] = idx + 1

    exercise_data["global_set_counter"] = len(all_sets_sorted)

