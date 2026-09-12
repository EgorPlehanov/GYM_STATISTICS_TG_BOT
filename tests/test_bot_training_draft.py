"""Тесты JSON-friendly FSM draft сценария тренировки."""

import json
from datetime import date, datetime

from app.bot.fsm.training import (
    TrainingDraft,
    TrainingDraftData,
    TrainingDraftExercise,
    TrainingDraftSet,
    draft_from_json,
    draft_to_json,
    draft_to_legacy_exercise_data,
    legacy_exercise_data_to_draft,
)


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
