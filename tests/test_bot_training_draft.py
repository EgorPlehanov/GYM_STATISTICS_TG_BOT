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
