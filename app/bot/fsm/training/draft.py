"""Операции над текущим FSM-черновиком тренировки."""

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from typing import Any

from aiogram.fsm.context import FSMContext


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
        training_date: дата тренировки. До выбора даты может быть None.
        comment: комментарий к тренировке.
        exercises: упражнения и подходы текущей тренировки.
    """

    training_id: int | None
    training_date: date | datetime | str | None
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
        current_exercise_id: последнее выбранное упражнение для быстрого добавления подхода.
        current_exercise_name: имя последнего выбранного упражнения.
        last_weight: последний сохраненный вес для кнопки повтора.
        last_repetitions: последнее сохраненное количество повторений.
    """

    message_id: int | None = None
    state_before_delete: str | None = None
    reply_markup_before_delete: dict[str, Any] | None = None
    current_exercise_id: int | None = None
    current_exercise_name: str | None = None
    last_weight: float | None = None
    last_repetitions: int | None = None


@dataclass(slots=True)
class TrainingSuggestions:
    """Подсказки, загруженные из backend для Telegram-сценария.

    Attributes:
        most_frequent_exercises: частые упражнения пользователя.
        weight_repetitions_modes: подсказки веса и повторений.
        training_dates: даты существующих тренировок в формате YYYY-MM-DD.
    """

    most_frequent_exercises: list[dict[str, Any]] = field(default_factory=list)
    weight_repetitions_modes: dict[str, Any] = field(default_factory=dict)
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
            training_date=_normalize_date_or_none(training_data.get("training_date")),
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


async def get_training_draft(state: FSMContext) -> TrainingDraft:
    """Возвращает типизированный draft из текущего aiogram FSMContext.

    Args:
        state: контекст aiogram FSM текущего пользователя.

    Returns:
        Типизированный draft, восстановленный из JSON-friendly ключа `training_draft`.

    Raises:
        KeyError: если в FSM еще нет `training_draft`.
    """
    data = await state.get_data()
    draft_data = data.get("training_draft")
    if draft_data is None:
        raise KeyError("В FSM data отсутствует training_draft")
    return draft_from_json(draft_data)


async def set_training_draft(
    state: FSMContext,
    draft: TrainingDraft,
) -> None:
    """Сохраняет типизированный draft в текущий FSMContext.

    Args:
        state: контекст aiogram FSM текущего пользователя.
        draft: типизированный draft тренировки.

    Returns:
        None. JSON-friendly draft записывается в ключ `training_draft`.
    """
    await state.update_data(training_draft=draft_to_json(draft))


def _normalize_json_value(value: Any) -> Any:
    """Рекурсивно приводит значение к JSON-friendly формату."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _normalize_json_value(asdict(value))
    if isinstance(value, dict):
        return {
            str(key): _normalize_json_value(item)
            for key, item in value.items()
        }
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


def _normalize_date_or_none(value: date | datetime | str | None) -> str | None:
    """Возвращает дату в формате YYYY-MM-DD или None."""
    if value is None:
        return None
    return _normalize_date(value)


def _normalize_datetime_or_none(value: datetime | str | None) -> str | None:
    """Возвращает время в ISO-формате или None."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value



