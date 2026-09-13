"""Адаптеры между strict API DTO тренировки и FSM draft."""

from datetime import date, datetime

from app.bot.api_client.schemas.trainings import (
    BotTraining,
    BotTrainingExercise,
    BotTrainingSet,
)

from .draft import (
    TrainingDraft,
    TrainingDraftData,
    TrainingDraftExercise,
    TrainingDraftSet,
)


def bot_training_to_draft(training: BotTraining) -> TrainingDraft:
    """Преобразует strict API DTO тренировки в FSM draft.

    Args:
        training: тренировка, полученная от internal API.

    Returns:
        FSM draft, который handlers используют как сценарный state.
    """
    return TrainingDraft(
        training=TrainingDraftData(
            training_id=training.training_id,
            training_date=training.training_date.isoformat(),
            comment=training.comment,
            exercises=[
                TrainingDraftExercise(
                    exercise_id=exercise.exercise_id,
                    exercise_name=exercise.exercise_name,
                    sets=[
                        TrainingDraftSet(
                            set_id=set_data.set_id,
                            set_number=set_data.set_number,
                            weight=set_data.weight,
                            repetitions=set_data.repetitions,
                            execution_time=(
                                set_data.execution_time.isoformat()
                                if set_data.execution_time is not None
                                else None
                            ),
                        )
                        for set_data in exercise.sets
                    ],
                )
                for exercise in training.exercises
            ],
        )
    )


def draft_to_bot_training(draft: TrainingDraft) -> BotTraining:
    """Преобразует FSM draft в strict API DTO тренировки.

    Args:
        draft: текущий FSM draft тренировки.

    Returns:
        DTO, который можно отправить в internal API без legacy FSM-формата.
    """
    return BotTraining(
        training_id=draft.training.training_id,
        training_date=_to_date(draft.training.training_date),
        comment=draft.training.comment,
        exercises=[
            BotTrainingExercise(
                exercise_id=exercise.exercise_id,
                exercise_name=exercise.exercise_name,
                sets=[
                    BotTrainingSet(
                        set_id=set_data.set_id,
                        set_number=set_data.set_number,
                        weight=set_data.weight,
                        repetitions=set_data.repetitions,
                        execution_time=_to_datetime_or_none(set_data.execution_time),
                    )
                    for set_data in exercise.sets
                ],
            )
            for exercise in draft.training.exercises
        ],
    )


def _to_date(value: date | datetime | str | None) -> date:
    """Возвращает date из date, datetime или ISO-строки."""
    if value is None:
        raise ValueError("Нельзя отправить тренировку без даты")
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _to_datetime_or_none(value: datetime | str | None) -> datetime | None:
    """Возвращает datetime из datetime, ISO-строки или None."""
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)
