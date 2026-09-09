"""Internal endpoints для сценариев упражнений Telegram-бота."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession
from app.api.schemas.internal_bot import InternalBotExerciseResponse
from app.domain.exercises.service import get_exercise_by_id
from app.domain.trainings.service import get_sorted_exercises_by_sets_count

router = APIRouter()


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
