"""Тесты JSON-friendly FSM draft сценария тренировки."""

import json
from datetime import date, datetime

from app.bot.fsm.training import (
    TrainingDraft,
    TrainingDraftData,
    TrainingDraftExercise,
    TrainingDraftSet,
    check_accept_addition_for_draft,
    draft_from_json,
    draft_to_json,
    draft_to_legacy_exercise_data,
    get_legacy_exercise_data,
    get_training_draft,
    get_weight_repetitions_modes_values_from_draft,
    legacy_exercise_data_to_draft,
    set_legacy_exercise_data,
    set_training_draft,
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
        "ui": {"message_id": 123},
        "suggestions": {
            "most_frequent_exercises": [{"id": 1, "name": "Присед"}],
            "weight_repetitions_modes": [],
            "training_dates": ["2026-09-12"],
        },
    }

    draft = draft_from_json(data)
    restored_data = draft_to_json(draft)

    assert draft.training.training_date == "2026-09-12"
    assert draft.training.exercises[0].sets[0].execution_time == "2026-09-12T19:00:00"
    assert restored_data == {
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
        "selection": {
            "mode": "add_set",
            "exercise_id": 1,
            "exercise_name": None,
            "weight": None,
            "repetitions": None,
            "sets_count": 1,
        },
        "edit": {
            "exercise_id": None,
            "exercise_name": None,
            "set_id": None,
            "set_number": None,
        },
        "ui": {
            "message_id": 123,
            "state_before_delete": None,
            "reply_markup_before_delete": None,
        },
        "suggestions": {
            "most_frequent_exercises": [{"id": 1, "name": "Присед"}],
            "weight_repetitions_modes": [],
            "training_dates": ["2026-09-12"],
        },
    }


def test_legacy_exercise_data_converts_to_training_draft() -> None:
    """Проверяет адаптацию старого `exercise_data` в типизированный draft."""
    legacy_data = {
        "id": 10,
        "user_id": 123456789,
        "date": date(2026, 9, 12),
        "comment": "Тест",
        "global_set_counter": 2,
        "exercises": {
            2: {
                "exercise_name": "Тяга",
                "local_set_counter": 1,
                "sets": {
                    1: {
                        "id": 22,
                        "set_number": 2,
                        "weight": 120.0,
                        "repetitions": 3,
                        "time": datetime(2026, 9, 12, 19, 10),
                    }
                },
            },
            "1": {
                "exercise_name": "Жим лежа",
                "local_set_counter": 1,
                "sets": {
                    "1": {
                        "id": 21,
                        "set_number": 1,
                        "weight": 80.0,
                        "repetitions": 8,
                        "time": "2026-09-12T18:30:00",
                    }
                },
            },
        },
    }

    draft = legacy_exercise_data_to_draft(legacy_data)

    assert draft.training.training_id == 10
    assert draft.training.training_date == "2026-09-12"
    assert draft.training.comment == "Тест"
    assert [exercise.exercise_id for exercise in draft.training.exercises] == [1, 2]
    assert draft.training.exercises[0].sets[0].execution_time == "2026-09-12T18:30:00"
    assert draft.training.exercises[1].sets[0].execution_time == "2026-09-12T19:10:00"


def test_training_draft_converts_to_legacy_exercise_data() -> None:
    """Проверяет адаптацию типизированного draft в старый `exercise_data`."""
    draft = TrainingDraft(
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
                        ),
                        TrainingDraftSet(
                            set_id=None,
                            set_number=2,
                            weight=82.5,
                            repetitions=6,
                            execution_time=None,
                        ),
                    ],
                )
            ],
        )
    )

    legacy_data = draft_to_legacy_exercise_data(draft, user_id=123456789)

    assert legacy_data == {
        "id": 10,
        "user_id": 123456789,
        "date": date(2026, 9, 12),
        "comment": "Тест",
        "global_set_counter": 2,
        "exercises": {
            1: {
                "exercise_name": "Жим лежа",
                "local_set_counter": 2,
                "sets": {
                    1: {
                        "id": 21,
                        "set_number": 1,
                        "weight": 80.0,
                        "repetitions": 8,
                        "time": datetime(2026, 9, 12, 18, 30),
                    },
                    2: {
                        "id": None,
                        "set_number": 2,
                        "weight": 82.5,
                        "repetitions": 6,
                        "time": None,
                    },
                },
            }
        },
    }


def test_legacy_exercise_data_round_trip_preserves_save_contract() -> None:
    """Проверяет round-trip старого формата через типизированный draft."""
    legacy_data = {
        "id": None,
        "user_id": 123456789,
        "date": date(2026, 9, 12),
        "comment": None,
        "global_set_counter": 1,
        "exercises": {
            1: {
                "exercise_name": "Присед",
                "local_set_counter": 1,
                "sets": {
                    1: {
                        "id": None,
                        "set_number": 1,
                        "weight": 100.0,
                        "repetitions": 5,
                        "time": datetime(2026, 9, 12, 19, 0),
                    }
                },
            }
        },
    }

    draft = legacy_exercise_data_to_draft(legacy_data)
    restored = draft_to_legacy_exercise_data(draft, user_id=legacy_data["user_id"])

    assert restored == legacy_data


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
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=10,
            training_date="2026-09-12",
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
                        )
                    ],
                )
            ],
        )
    )
    draft.selection.mode = TrainingMode.EDIT_SET.value
    draft.selection.weight = 80.0
    draft.selection.repetitions = 8
    draft.edit.exercise_id = 1
    draft.edit.set_id = 1

    assert not check_accept_addition_for_draft(draft)

    draft.selection.repetitions = 9

    assert check_accept_addition_for_draft(draft)


def test_weight_repetitions_modes_values_from_draft_uses_string_keys() -> None:
    """Проверяет получение подсказок из JSON-friendly dict со строковыми ключами."""
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=10,
            training_date="2026-09-12",
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
                        )
                    ],
                )
            ],
        )
    )
    draft.selection.exercise_id = 1
    draft.suggestions.weight_repetitions_modes = {
        "1": {
            "max_exercise_order": 1,
            "sets_modes": {
                "1": {
                    "weight_mode": 82.5,
                    "repetitions_mode": 6,
                }
            },
        }
    }

    assert get_weight_repetitions_modes_values_from_draft(
        draft,
        is_weight=True,
        is_repetitions=True,
    ) == ("82.5", "6")


async def test_get_training_draft_reads_legacy_fsm_context() -> None:
    """Проверяет чтение типизированного draft из текущего legacy FSMContext."""
    state = FakeFSMContext(
        {
            "exercise_data": {
                "id": 10,
                "user_id": 123456789,
                "date": date(2026, 9, 12),
                "comment": "Тест",
                "global_set_counter": 1,
                "exercises": {
                    1: {
                        "exercise_name": "Жим лежа",
                        "local_set_counter": 1,
                        "sets": {
                            1: {
                                "id": 21,
                                "set_number": 1,
                                "weight": 80.0,
                                "repetitions": 8,
                                "time": datetime(2026, 9, 12, 18, 30),
                            }
                        },
                    }
                },
            },
            "mode": TrainingMode.ADD_SET,
            "cur_exercise_id": 1,
            "cur_exercise_name": "Жим лежа",
            "weight": 82.5,
            "repetitions": 6,
            "sets_count": 2,
            "message_id": 500,
            "training_date": [date(2026, 9, 12)],
        }
    )

    draft = await get_training_draft(state)

    assert draft.training.training_id == 10
    assert draft.training.training_date == "2026-09-12"
    assert draft.training.exercises[0].sets[0].execution_time == "2026-09-12T18:30:00"
    assert draft.selection.mode == "add_set"
    assert draft.selection.exercise_id == 1
    assert draft.selection.weight == 82.5
    assert draft.ui.message_id == 500
    assert draft.suggestions.training_dates == ["2026-09-12"]


async def test_set_training_draft_writes_legacy_fsm_context() -> None:
    """Проверяет сохранение типизированного draft обратно в legacy FSMContext."""
    state = FakeFSMContext(
        {
            "exercise_data": {
                "id": None,
                "user_id": 123456789,
                "date": date(2026, 9, 12),
                "comment": None,
                "global_set_counter": 0,
                "exercises": {},
            }
        }
    )
    draft = TrainingDraft(
        training=TrainingDraftData(
            training_id=10,
            training_date="2026-09-13",
            comment="Новая дата",
            exercises=[
                TrainingDraftExercise(
                    exercise_id=1,
                    exercise_name="Жим лежа",
                    sets=[
                        TrainingDraftSet(
                            set_id=None,
                            set_number=1,
                            weight=80.0,
                            repetitions=8,
                            execution_time="2026-09-13T18:30:00",
                        )
                    ],
                )
            ],
        )
    )
    draft.selection.mode = "add_set"
    draft.selection.exercise_id = 1
    draft.selection.exercise_name = "Жим лежа"
    draft.selection.weight = 80.0
    draft.selection.repetitions = 8
    draft.selection.sets_count = 1
    draft.ui.message_id = 501
    draft.suggestions.training_dates = ["2026-09-13"]

    await set_training_draft(state, draft)

    assert state.data["mode"] == TrainingMode.ADD_SET
    assert state.data["cur_exercise_id"] == 1
    assert state.data["message_id"] == 501
    assert state.data["training_date"] == [date(2026, 9, 13)]
    assert state.data["exercise_data"] == {
        "id": 10,
        "user_id": 123456789,
        "date": date(2026, 9, 13),
        "comment": "Новая дата",
        "global_set_counter": 1,
        "exercises": {
            1: {
                "exercise_name": "Жим лежа",
                "local_set_counter": 1,
                "sets": {
                    1: {
                        "id": None,
                        "set_number": 1,
                        "weight": 80.0,
                        "repetitions": 8,
                        "time": datetime(2026, 9, 13, 18, 30),
                    }
                },
            }
        },
    }


async def test_legacy_exercise_data_helpers_read_and_write_fsm_context() -> None:
    """Проверяет короткие helpers для прямой работы с legacy `exercise_data`."""
    state = FakeFSMContext({})
    exercise_data = {
        "id": None,
        "user_id": 123456789,
        "date": date(2026, 9, 12),
        "comment": None,
        "global_set_counter": 0,
        "exercises": {},
    }

    await set_legacy_exercise_data(state, exercise_data)

    assert await get_legacy_exercise_data(state) == exercise_data
