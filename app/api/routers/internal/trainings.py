"""Internal endpoints для сценариев тренировок Telegram-бота."""

from datetime import date, datetime

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.schemas.internal.trainings import (
    InternalBotTrainingByDateResponse,
    InternalBotTrainingSaveRequest,
    InternalBotTrainingSaveResponse,
    InternalBotTrainingStartContextResponse,
)
from app.domain.trainings.service import (
    check_training_exists_for_user_and_date,
    delete_training_by_id,
    get_exercises_weight_repetitions_modes,
    get_sorted_exercises_by_sets_count,
    get_training_data_by_date_and_user,
    get_training_date_by_user_id,
    save_training_data,
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
        weight_repetitions_modes=weight_repetitions_modes,
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
        training_data = await get_training_data_by_date_and_user(
            session=session,
            user_id=telegram_id,
            date=training_date,
        )
    else:
        training_data = {
            "id": None,
            "user_id": telegram_id,
            "date": training_date,
            "comment": None,
            "global_set_counter": 0,
            "exercises": {},
        }

    return InternalBotTrainingByDateResponse(
        exists=is_exists,
        training_data=training_data,
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
    training_id, updated, created = await save_training_data(
        session=session,
        training_data=_deserialize_training_data(payload.training_data),
    )
    return InternalBotTrainingSaveResponse(
        training_id=training_id,
        updated=updated,
        created=created,
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


def _deserialize_training_data(training_data: dict) -> dict:
    """Восстанавливает старый FSM-формат тренировки после JSON-запроса.

    Args:
        training_data: JSON-словарь с ISO-датами и строковыми ключами.

    Returns:
        структура с `date`, `datetime` в подходах и числовыми ключами `exercises`/`sets`.
    """
    restored = dict(training_data)
    if restored.get("date") is not None:
        restored["date"] = date.fromisoformat(restored["date"])

    exercises = {}
    for exercise_id, exercise_data in restored.get("exercises", {}).items():
        exercise = dict(exercise_data)
        exercise["sets"] = {
            int(set_id): _deserialize_set_data(set_data)
            for set_id, set_data in exercise.get("sets", {}).items()
        }
        exercises[int(exercise_id)] = exercise

    restored["exercises"] = exercises
    return restored


def _deserialize_set_data(set_data: dict) -> dict:
    """Восстанавливает данные подхода после JSON-запроса."""
    restored = dict(set_data)
    if restored.get("time") is not None:
        restored["time"] = datetime.fromisoformat(restored["time"])
    return restored
