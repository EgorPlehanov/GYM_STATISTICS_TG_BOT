"""Репозиторий упражнений."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Exercise


class ExerciseRepository:
    """Доступ к данным справочника упражнений."""


async def get_exercise_by_id(
    session: AsyncSession,
    exercise_id: int,
) -> Exercise | None:
    """Возвращает упражнение по id.

    Args:
        `exercise_id` - внутренний id упражнения из справочника.

    Returns:
        объект упражнения или `None`, если запись не найдена.
    """
    result = await session.execute(select(Exercise).where(Exercise.id == exercise_id))
    return result.scalar()
