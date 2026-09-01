"""Сервис упражнений."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Exercise
from app.db.repositories import exercises as exercise_repository


class ExercisesService:
    """Бизнес-сценарии для упражнений."""

    get_exercise_by_id = staticmethod(exercise_repository.get_exercise_by_id)


async def get_exercise_by_id(session: AsyncSession, exercise_id: int) -> Exercise | None:
    """Возвращает упражнение по id."""
    return await exercise_repository.get_exercise_by_id(session, exercise_id)


async def get_exercise(session: AsyncSession, exercise_id: int) -> Exercise | None:
    """Возвращает упражнение по id."""
    return await exercise_repository.get_exercise_by_id(session, exercise_id)
