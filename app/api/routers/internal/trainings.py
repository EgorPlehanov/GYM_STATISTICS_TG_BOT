"""Internal endpoints для сценариев тренировок Telegram-бота."""

from datetime import date, datetime

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.schemas.internal.trainings import (
    InternalBotTrainingByDateResponse,
    InternalBotTrainingData,
    InternalBotTrainingExercise,
    InternalBotTrainingExerciseMode,
    InternalBotTrainingSaveOutcome,
    InternalBotTrainingSaveRequest,
    InternalBotTrainingSaveResponse,
    InternalBotTrainingSet,
    InternalBotTrainingStartContextResponse,
)
from app.domain.trainings.service import (
    check_training_exists_for_user_and_date,
    delete_training_by_id,
    get_exercises_weight_repetitions_modes,
    get_sorted_exercises_by_sets_count,
    get_training_data_by_date_and_user,
    get_training_date_by_user_id,
    save_training,
)

router = APIRouter()


@router.get("/bot/trainings/start-context", response_model=InternalBotTrainingStartContextResponse)
async def get_bot_training_start_context(
    session: DbSession,
    telegram_id: int,
    page_size: int = 15,
    last_training_count: int = 12,
) -> InternalBotTrainingStartContextResponse:
    """Возвращает данные, необходимые для старта сценария `/training`.

    Args:
        telegram_id: Telegram user id пользователя.
        page_size: количество частых упражнений для первичной клавиатуры.
        last_training_count: количество последних тренировок для расчета подсказок.

    Returns:
        стартовый контекст FSM-сценария тренировки.
    """
    most_frequent_exercises = await get_sorted_exercises_by_sets_count(
        session=session,
        user_id=telegram_id,
        page_size=page_size,
    )
    weight_repetitions_modes = await get_exercises_weight_repetitions_modes(
        session=session,
        user_id=telegram_id,
        last_training_count=last_training_count,
    )
    return InternalBotTrainingStartContextResponse(
        most_frequent_exercises=most_frequent_exercises,
        weight_repetitions_modes={
            exercise_id: InternalBotTrainingExerciseMode.model_validate(exercise_mode)
            for exercise_id, exercise_mode in weight_repetitions_modes.items()
        },
    )


@router.get("/bot/trainings/dates", response_model=list[date])
async def get_bot_training_dates(
    session: DbSession,
    telegram_id: int,
) -> list[date]:
    """Возвращает даты тренировок пользователя для календаря Telegram-бота.

    Args:
        telegram_id: Telegram user id, для которого нужно получить даты.

    Returns:
        список дат тренировок пользователя.
    """
    return await get_training_date_by_user_id(session=session, user_id=telegram_id)


@router.get("/bot/trainings/by-date", response_model=InternalBotTrainingByDateResponse)
async def get_bot_training_by_date(
    session: DbSession,
    telegram_id: int,
    training_date: date,
) -> InternalBotTrainingByDateResponse:
    """Возвращает существующую тренировку или пустую структуру для новой даты.

    Args:
        telegram_id: Telegram user id пользователя.
        training_date: дата, выбранная в Telegram-боте.

    Returns:
        данные тренировки и признак существования записи в базе.
    """
    is_exists = await check_training_exists_for_user_and_date(
        session=session,
        user_id=telegram_id,
        date=training_date,
    )
    if is_exists:
        repository_training_data = await get_training_data_by_date_and_user(
            session=session,
            user_id=telegram_id,
            date=training_date,
        )
        training = _repository_training_data_to_dto(repository_training_data)
    else:
        training = InternalBotTrainingData(
            training_id=None,
            training_date=training_date,
            comment=None,
            exercises=[],
        )

    return InternalBotTrainingByDateResponse(
        exists=is_exists,
        training=training,
    )


@router.post("/bot/trainings", response_model=InternalBotTrainingSaveResponse)
async def save_bot_training(
    payload: InternalBotTrainingSaveRequest,
    session: DbSession,
) -> InternalBotTrainingSaveResponse:
    """Сохраняет тренировку из Telegram-бота через backend API.

    Args:
        payload: JSON-совместимая структура тренировки из FSM бота.

    Returns:
        результат сохранения из domain service.
    """
    training_id, outcome = await save_training(
        session=session,
        training_data=_dto_to_repository_training_data(
            payload.training,
            telegram_id=payload.telegram_id,
        ),
    )
    return InternalBotTrainingSaveResponse(
        training_id=training_id,
        outcome=InternalBotTrainingSaveOutcome(outcome.value),
    )


@router.delete("/bot/trainings/{training_id}")
async def delete_bot_training(
    training_id: int,
    session: DbSession,
) -> dict[str, str]:
    """Удаляет тренировку из сценария Telegram-бота.

    Args:
        training_id: id тренировки, которую нужно удалить.

    Returns:
        короткий статус успешного выполнения операции.
    """
    await delete_training_by_id(session=session, training_id=training_id)
    return {"status": "ok"}


def _repository_training_data_to_dto(
    training_data: dict,
) -> InternalBotTrainingData:
    """Преобразует repository-format тренировки в strict DTO internal API.

    Args:
        training_data: структура, которую пока возвращает repository/domain слой.

    Returns:
        DTO без legacy-счетчиков, словарей по id и `user_id` внутри тренировки.
    """
    return InternalBotTrainingData(
        training_id=training_data.get("id"),
        training_date=_to_date(training_data["date"]),
        comment=training_data.get("comment"),
        exercises=[
            InternalBotTrainingExercise(
                exercise_id=int(exercise_id),
                exercise_name=exercise_data["exercise_name"],
                sets=[
                    InternalBotTrainingSet(
                        set_id=set_data.get("id"),
                        set_number=set_data["set_number"],
                        weight=set_data["weight"],
                        repetitions=set_data["repetitions"],
                        execution_time=_to_datetime_or_none(set_data.get("time")),
                    )
                    for _, set_data in sorted(
                        exercise_data.get("sets", {}).items(),
                        key=lambda item: int(item[0]),
                    )
                ],
            )
            for exercise_id, exercise_data in sorted(
                training_data.get("exercises", {}).items(),
                key=lambda item: int(item[0]),
            )
        ],
    )


def _dto_to_repository_training_data(
    training: InternalBotTrainingData,
    *,
    telegram_id: int,
) -> dict:
    """Преобразует strict DTO internal API в текущий repository-format.

    Args:
        training: strict DTO тренировки из Telegram-бота.
        telegram_id: Telegram user id владельца тренировки.

    Returns:
        Структура, которую пока ожидает domain/repository слой.
    """
    exercises = {}
    global_set_counter = 0
    for exercise in training.exercises:
        legacy_sets = {}
        for local_set_number, set_data in enumerate(exercise.sets, start=1):
            legacy_sets[local_set_number] = {
                "id": set_data.set_id,
                "set_number": set_data.set_number,
                "weight": set_data.weight,
                "repetitions": set_data.repetitions,
                "time": set_data.execution_time,
            }
            global_set_counter = max(global_set_counter, set_data.set_number)

        exercises[exercise.exercise_id] = {
            "exercise_name": exercise.exercise_name,
            "local_set_counter": len(legacy_sets),
            "sets": legacy_sets,
        }

    return {
        "id": training.training_id,
        "user_id": telegram_id,
        "date": training.training_date,
        "comment": training.comment,
        "global_set_counter": global_set_counter,
        "exercises": exercises,
    }


def _to_date(value: date | datetime | str) -> date:
    """Возвращает дату из date, datetime или ISO-строки."""
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
