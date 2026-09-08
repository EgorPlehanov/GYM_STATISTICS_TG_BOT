"""Router служебного internal API."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSession, get_internal_service
from app.api.schemas.internal_bot import (
    InternalBotExerciseResponse,
    InternalBotUserEnsureRequest,
    InternalBotUserEnsureResponse,
)
from app.domain.exercises.service import get_exercise_by_id
from app.domain.trainings.service import get_sorted_exercises_by_sets_count
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
