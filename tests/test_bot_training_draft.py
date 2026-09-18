"""Тесты JSON-friendly FSM draft сценария тренировки."""

import json
from datetime import date, datetime

import pytest

from app.bot.api_client.schemas.trainings import (
    BotTraining,
    BotTrainingExercise,
    BotTrainingSet,
)
from app.bot.fsm.training import (
    TrainingDraft,
    TrainingDraftData,
    TrainingDraftExercise,
    TrainingDraftSet,
    TrainingExerciseModeSuggestion,
    TrainingSetModeSuggestion,
    TrainingSuggestedExercise,
    add_exercise_to_draft,
    add_set_to_draft,
    bot_training_to_draft,
    check_accept_addition_for_draft,
    delete_all_exercise_sets_from_draft,
    delete_all_exercises_from_draft,
    delete_set_from_draft,
    draft_from_json,
    draft_to_bot_training,
    draft_to_json,
    get_draft_exercise,
    get_draft_set_by_local_id,
    get_training_draft,
    get_weight_repetitions_modes_values_from_draft,
    has_draft_exercises,
    recalculate_draft_set_numbers,
    set_training_draft,
    update_set_in_draft,
)
from app.bot.fsm.training.states import TrainingMode


class FakeFSMContext:
    """Минимальная заглушка aiogram FSMContext для тестов draft helpers."""

    def __init__(self, data: dict):
        """Сохраняет стартовые данные FSM.

        Args:
            data: начальный словарь FSM data.
        """
        self.data = data

    async def get_data(self) -> dict:
        """Возвращает текущие данные FSM."""
        return self.data

    async def update_data(self, **kwargs) -> None:
        """Обновляет данные FSM как `FSMContext.update_data`.

        Args:
            kwargs: значения, которые нужно записать в FSM data.
        """
        self.data.update(kwargs)


def test_training_draft_serializes_dates_to_json_friendly_strings() -> None:
    """Проверяет нормализацию date/datetime при сериализации FSM draft."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=10,
            training_date=date(2026, 9, 12),
            comment="Тяжелая тренировка",
            exercises=[
                TrainingDraftExercise(
                    exercise_id=1,
                    exercise_name="Жим лежа",
                    sets=[
                        TrainingDraftSet(
                            set_id=100,
                            set_number=1,
                            weight=80.5,
                            repetitions=8,
                            execution_time=datetime(2026, 9, 12, 18, 30, 15),
                        )
                    ],
                )
            ],
        )
    )

    data = draft_to_json(draft)

    assert data["training"]["training_date"] == "2026-09-12"
    assert (
        data["training"]["exercises"][0]["sets"][0]["execution_time"]
        == "2026-09-12T18:30:15"
    )
    json.dumps(data)


def test_training_draft_round_trip_from_json() -> None:
    """Проверяет восстановление типизированного draft из JSON-compatible словаря."""
    data = {
        "training": {
            "training_id": None,
            "training_date": "2026-09-12",
            "comment": None,
            "exercises": [
                {
                    "exercise_id": 1,
                    "exercise_name": "Присед",
                    "sets": [
                        {
                            "set_id": None,
                            "set_number": 1,
                            "weight": 100.0,
                            "repetitions": 5,
                            "execution_time": "2026-09-12T19:00:00",
                        }
                    ],
                }
            ],
        },
        "selection": {"mode": "add_set", "exercise_id": 1, "sets_count": 1},
        "edit": {},
        "ui": {
            "message_id": 123,
            "current_exercise_id": 1,
            "current_exercise_name": "Присед",
            "last_weight": 100.0,
            "last_repetitions": 5,
        },
        "suggestions": {
            "most_frequent_exercises": [
                {"id": 1, "name": "Присед", "description": "Базовое упражнение"}
            ],
            "weight_repetitions_modes": {
                "1": {
                    "max_exercise_order": 1,
                    "sets_modes": {
                        "1": {"weight_mode": 100.0, "repetitions_mode": 5}
                    },
                }
            },
            "training_dates": ["2026-09-12"],
        },
    }

    draft = draft_from_json(data)
    restored_data = draft_to_json(draft)

    assert draft.training.training_date == "2026-09-12"
    assert draft.training.exercises[0].sets[0].execution_time == "2026-09-12T19:00:00"
    assert restored_data["ui"]["current_exercise_name"] == "Присед"
    assert restored_data["ui"]["last_weight"] == 100.0
    assert draft.suggestions.most_frequent_exercises == [
        TrainingSuggestedExercise(
            id=1,
            name="Присед",
            description="Базовое упражнение",
        )
    ]
    assert draft.suggestions.weight_repetitions_modes == {
        1: TrainingExerciseModeSuggestion(
            max_exercise_order=1,
            sets_modes={
                1: TrainingSetModeSuggestion(weight_mode=100.0, repetitions_mode=5)
            },
        )
    }
    assert restored_data["suggestions"]["weight_repetitions_modes"] == {
        "1": {
            "max_exercise_order": 1,
            "sets_modes": {
                "1": {"weight_mode": 100.0, "repetitions_mode": 5}
            },
        }
    }


def test_bot_training_dto_converts_to_training_draft() -> None:
    """Проверяет адаптацию strict API DTO в FSM draft."""
    training = BotTraining(
        training_id=10,
        training_date=date(2026, 9, 12),
        comment="Тест",
        exercises=[
            BotTrainingExercise(
                exercise_id=1,
                exercise_name="Жим лежа",
                sets=[
                    BotTrainingSet(
                        set_id=21,
                        set_number=1,
                        weight=80.0,
                        repetitions=8,
                        execution_time=datetime(2026, 9, 12, 18, 30),
                    )
                ],
            )
        ],
    )

    draft = bot_training_to_draft(training)

    assert draft.training.training_id == 10
    assert draft.training.training_date == "2026-09-12"
    assert draft.training.exercises[0].sets[0].execution_time == "2026-09-12T18:30:00"


def test_training_draft_converts_to_bot_training_dto() -> None:
    """Проверяет адаптацию FSM draft в strict API DTO."""
    draft = _build_training_draft()

    training = draft_to_bot_training(draft)

    assert training.training_id == 10
    assert training.training_date == date(2026, 9, 12)
    assert training.exercises[0].sets[0].execution_time == datetime(
        2026, 9, 12, 18, 30
    )


def test_training_draft_without_date_cannot_be_sent_to_api() -> None:
    """Проверяет явную ошибку при отправке незавершенного draft в API."""
    draft = TrainingDraft(training=TrainingDraftData(training_id=None, training_date=None))

    with pytest.raises(ValueError, match="без даты"):
        draft_to_bot_training(draft)


def test_check_accept_addition_for_draft_allows_complete_add_exercise() -> None:
    """Проверяет подтверждение добавления упражнения по draft."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=None,
            training_date="2026-09-12",
        )
    )
    draft.selection.mode = TrainingMode.ADD_EXERCISE.value
    draft.selection.exercise_id = 1
    draft.selection.weight = 80.0
    draft.selection.repetitions = 8

    assert check_accept_addition_for_draft(draft)


def test_check_accept_addition_for_draft_rejects_incomplete_add_set() -> None:
    """Проверяет запрет подтверждения подхода без повторений."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=None,
            training_date="2026-09-12",
        )
    )
    draft.selection.mode = TrainingMode.ADD_SET.value
    draft.selection.weight = 80.0

    assert not check_accept_addition_for_draft(draft)


def test_check_accept_addition_for_draft_compares_edited_set() -> None:
    """Проверяет подтверждение редактирования только при изменении подхода."""
    draft = _build_training_draft()
    draft.selection.mode = TrainingMode.EDIT_SET.value
    draft.selection.weight = 80.0
    draft.selection.repetitions = 8
    draft.edit.exercise_id = 1
    draft.edit.set_id = 1

    assert not check_accept_addition_for_draft(draft)

    draft.selection.repetitions = 9

    assert check_accept_addition_for_draft(draft)


def test_weight_repetitions_modes_values_from_draft_uses_typed_suggestions() -> None:
    """Проверяет получение подсказок из типизированных моделей draft."""
    draft = _build_training_draft()
    draft.selection.exercise_id = 1
    draft.suggestions.weight_repetitions_modes = {
        1: TrainingExerciseModeSuggestion(
            max_exercise_order=1,
            sets_modes={
                1: TrainingSetModeSuggestion(weight_mode=82.5, repetitions_mode=6)
            },
        )
    }

    assert get_weight_repetitions_modes_values_from_draft(
        draft,
        is_weight=True,
        is_repetitions=True,
    ) == ("82.5", "6")


def test_weight_repetitions_modes_values_from_draft_uses_ui_fallback() -> None:
    """Проверяет подсказки для быстрого добавления подхода к последнему упражнению."""
    draft = _build_training_draft()
    draft.ui.current_exercise_id = 1
    draft.suggestions.weight_repetitions_modes = {
        1: TrainingExerciseModeSuggestion(
            max_exercise_order=1,
            sets_modes={
                1: TrainingSetModeSuggestion(weight_mode=80.0, repetitions_mode=8)
            },
        )
    }

    assert get_weight_repetitions_modes_values_from_draft(draft, is_weight=True) == "80.0"


def test_draft_operations_add_exercise_and_sets() -> None:
    """Проверяет добавление упражнения и подходов напрямую в draft."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=None,
            training_date="2026-09-12",
        )
    )

    add_exercise_to_draft(draft, exercise_id=1, exercise_name="Жим лежа")
    add_exercise_to_draft(draft, exercise_id=1, exercise_name="Жим лежа")
    add_set_to_draft(
        draft,
        exercise_id=1,
        weight=80.0,
        repetitions=8,
        execution_time=datetime(2026, 9, 12, 18, 30),
    )
    add_set_to_draft(
        draft,
        exercise_id=1,
        weight=82.5,
        repetitions=6,
        execution_time=None,
    )

    assert len(draft.training.exercises) == 1
    assert [set_data.set_number for set_data in draft.training.exercises[0].sets] == [1, 2]
    assert draft.training.exercises[0].sets[0].execution_time == "2026-09-12T18:30:00"


def test_draft_operations_update_set_by_local_id() -> None:
    """Проверяет изменение подхода по локальному номеру внутри упражнения."""
    draft = _build_training_draft()

    updated = update_set_in_draft(
        draft,
        exercise_id=1,
        set_id=1,
        new_weight=82.5,
        new_repetitions=6,
    )

    assert updated
    assert draft.training.exercises[0].sets[0].weight == 82.5
    assert draft.training.exercises[0].sets[0].repetitions == 6
    assert not update_set_in_draft(draft, exercise_id=99, set_id=1, new_weight=90.0)


def test_draft_operations_delete_set_and_recalculate_numbers() -> None:
    """Проверяет удаление подхода и пересчет глобальных номеров."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=10,
            training_date="2026-09-12",
            exercises=[
                TrainingDraftExercise(
                    exercise_id=1,
                    exercise_name="Жим лежа",
                    sets=[
                        TrainingDraftSet(None, 1, 80.0, 8),
                        TrainingDraftSet(None, 2, 82.5, 6),
                    ],
                ),
                TrainingDraftExercise(
                    exercise_id=2,
                    exercise_name="Присед",
                    sets=[TrainingDraftSet(None, 3, 100.0, 5)],
                ),
            ],
        )
    )

    delete_set_from_draft(draft, exercise_id=1, set_id=1)

    set_numbers = [
        set_data.set_number
        for exercise in draft.training.exercises
        for set_data in exercise.sets
    ]
    assert set_numbers == [1, 2]
    assert draft.training.exercises[0].sets[0].weight == 82.5


def test_draft_operations_delete_exercise_and_all_exercises() -> None:
    """Проверяет удаление упражнения и очистку всего draft."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=10,
            training_date="2026-09-12",
            exercises=[
                TrainingDraftExercise(
                    exercise_id=1,
                    exercise_name="Жим лежа",
                    sets=[TrainingDraftSet(None, 1, 80.0, 8)],
                ),
                TrainingDraftExercise(
                    exercise_id=2,
                    exercise_name="Присед",
                    sets=[TrainingDraftSet(None, 2, 100.0, 5)],
                ),
            ],
        )
    )

    delete_all_exercise_sets_from_draft(draft, exercise_id=1)

    assert [exercise.exercise_id for exercise in draft.training.exercises] == [2]
    assert draft.training.exercises[0].sets[0].set_number == 1

    delete_all_exercises_from_draft(draft)

    assert draft.training.exercises == []


def test_recalculate_draft_set_numbers_preserves_exercise_order() -> None:
    """Проверяет явный пересчет номеров подходов в порядке упражнений."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=10,
            training_date="2026-09-12",
            exercises=[
                TrainingDraftExercise(
                    exercise_id=2,
                    exercise_name="Присед",
                    sets=[TrainingDraftSet(None, 9, 100.0, 5)],
                ),
                TrainingDraftExercise(
                    exercise_id=1,
                    exercise_name="Жим лежа",
                    sets=[TrainingDraftSet(None, 3, 80.0, 8)],
                ),
            ],
        )
    )

    recalculate_draft_set_numbers(draft)

    set_numbers = [
        set_data.set_number
        for exercise in draft.training.exercises
        for set_data in exercise.sets
    ]
    assert set_numbers == [1, 2]


def test_draft_read_helpers_find_exercise_and_set() -> None:
    """Проверяет read-only helpers для доступа к данным draft."""
    draft = _build_training_draft()

    exercise = get_draft_exercise(draft, exercise_id=1)
    set_data = get_draft_set_by_local_id(draft, exercise_id=1, set_id=1)

    assert has_draft_exercises(draft)
    assert exercise.exercise_name == "Жим лежа"
    assert set_data.weight == 80.0


async def test_get_training_draft_reads_training_draft_fsm_context() -> None:
    """Проверяет чтение типизированного draft из ключа `training_draft`."""
    expected_draft = _build_training_draft()
    expected_draft.selection.mode = TrainingMode.ADD_SET.value
    expected_draft.selection.exercise_id = 1
    expected_draft.ui.message_id = 500
    expected_draft.suggestions.training_dates = ["2026-09-12"]
    state = FakeFSMContext({"training_draft": draft_to_json(expected_draft)})

    draft = await get_training_draft(state)

    assert draft.training.training_id == 10
    assert draft.selection.mode == "add_set"
    assert draft.ui.message_id == 500
    assert draft.suggestions.training_dates == ["2026-09-12"]


async def test_get_training_draft_requires_training_draft_key() -> None:
    """Проверяет явную ошибку, если сценарий не инициализировал draft."""
    state = FakeFSMContext({})

    with pytest.raises(KeyError, match="training_draft"):
        await get_training_draft(state)


async def test_set_training_draft_writes_training_draft_fsm_context() -> None:
    """Проверяет сохранение типизированного draft только в новый FSM-ключ."""
    state = FakeFSMContext({})
    draft = _build_training_draft()
    draft.selection.mode = "add_set"
    draft.selection.exercise_id = 1
    draft.selection.exercise_name = "Жим лежа"
    draft.selection.weight = 80.0
    draft.selection.repetitions = 8
    draft.selection.sets_count = 1
    draft.ui.message_id = 501
    draft.ui.current_exercise_id = 1
    draft.ui.current_exercise_name = "Жим лежа"
    draft.ui.last_weight = 80.0
    draft.ui.last_repetitions = 8
    draft.suggestions.training_dates = ["2026-09-12"]

    await set_training_draft(state, draft)

    assert set(state.data) == {"training_draft"}
    assert state.data["training_draft"]["selection"]["mode"] == "add_set"
    assert state.data["training_draft"]["ui"]["message_id"] == 501
    assert state.data["training_draft"]["ui"]["last_repetitions"] == 8


def _build_training_draft() -> TrainingDraft:
    """Создает заполненный draft тренировки для тестов.

    Returns:
        Draft с одной тренировкой, одним упражнением и одним подходом.
    """
    return TrainingDraft(
        training=TrainingDraftData(
            training_id=10,
            training_date="2026-09-12",
            comment="Тест",
            exercises=[
                TrainingDraftExercise(
                    exercise_id=1,
                    exercise_name="Жим лежа",
                    sets=[
                        TrainingDraftSet(
                            set_id=21,
                            set_number=1,
                            weight=80.0,
                            repetitions=8,
                            execution_time="2026-09-12T18:30:00",
                        )
                    ],
                )
            ],
        )
    )
