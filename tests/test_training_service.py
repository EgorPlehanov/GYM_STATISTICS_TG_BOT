"""Тесты доменного сервиса тренировок."""

import pytest

from app.domain.trainings import service as trainings_service
from app.domain.trainings.schemas import TrainingSaveOutcome


@pytest.mark.parametrize(
    ("updated", "created", "expected_outcome"),
    [
        (True, True, TrainingSaveOutcome.CREATED),
        (True, False, TrainingSaveOutcome.UPDATED),
        (False, False, TrainingSaveOutcome.UNCHANGED),
    ],
)
async def test_save_training_maps_repository_flags_to_semantic_outcome(
    monkeypatch,
    updated: bool,
    created: bool,
    expected_outcome: TrainingSaveOutcome,
) -> None:
    """Проверяет приоритет создания тренировки над изменениями ее подходов."""

    async def fake_save_training_data(session, training_data):
        """Возвращает технический результат репозитория без обращения к БД."""
        return 42, updated, created

    monkeypatch.setattr(
        trainings_service.training_repository,
        "save_training_data",
        fake_save_training_data,
    )

    training_id, outcome = await trainings_service.save_training(
        session=object(),
        training_data={},
    )

    assert training_id == 42
    assert outcome is expected_outcome
