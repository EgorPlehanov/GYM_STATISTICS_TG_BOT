"""Router служебного internal API."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSession, get_internal_service
from app.api.schemas.internal_bot import (
    InternalBotExerciseResponse,
    InternalBotTrainingByDateResponse,
    InternalBotUserEnsureRequest,
    InternalBotUserEnsureResponse,
)
from app.domain.exercises.service import get_exercise_by_id
from app.domain.trainings.service import (
    check_training_exists_for_user_and_date,
    get_sorted_exercises_by_sets_count,
    get_training_data_by_date_and_user,
    get_training_date_by_user_id,
)
from app.domain.users.service import create_user_if_not_exists

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    dependencies=[Depends(get_internal_service)],
)


@router.get("/health")
async def internal_health_check() -> dict[str, str]:
    """Проверяет service-to-service авторизацию internal API.

    Returns:
        короткий JSON-ответ без бизнес-данных.
    """
    return {"status": "ok"}


@router.post("/bot/users/ensure", response_model=InternalBotUserEnsureResponse)
async def ensure_bot_user(
    payload: InternalBotUserEnsureRequest,
    session: DbSession,
) -> InternalBotUserEnsureResponse:
    """Создает пользователя из Telegram-бота, если его еще нет.

    Args:
        payload: Telegram user id и профильные данные из update-а бота.

    Returns:
        признак того, была ли создана новая запись пользователя.
    """
    created = await create_user_if_not_exists(
        session=session,
        user_id=payload.telegram_id,
        name=payload.name,
        language_code=payload.language_code,
    )
    return InternalBotUserEnsureResponse(created=created)


@router.get("/bot/exercises", response_model=list[InternalBotExerciseResponse])
async def get_bot_exercises(
    session: DbSession,
    telegram_id: int,
    page_size: int = 50,
    page_num: int = 0,
    substring: str | None = None,
) -> list[InternalBotExerciseResponse]:
    """Возвращает упражнения для выбора в Telegram-боте.

    Args:
        telegram_id: Telegram user id, по которому упражнения сортируются по частоте.
        page_size: размер страницы для inline-поиска.
        page_num: номер страницы, начиная с 0.
        substring: строка поиска по названию и описанию упражнения.

    Returns:
        список упражнений, отсортированный под сценарий выбора упражнения в боте.
    """
    return await get_sorted_exercises_by_sets_count(
        session=session,
        user_id=telegram_id,
        page_size=page_size,
        page_num=page_num,
        substring=substring,
    )


@router.get("/bot/exercises/{exercise_id}", response_model=InternalBotExerciseResponse)
async def get_bot_exercise(
    session: DbSession,
    exercise_id: int,
) -> InternalBotExerciseResponse:
    """Возвращает упражнение по id для Telegram-бота."""
    exercise = await get_exercise_by_id(session=session, exercise_id=exercise_id)
    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Упражнение не найдено",
        )
    return exercise


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
    training_date: datetime,
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
