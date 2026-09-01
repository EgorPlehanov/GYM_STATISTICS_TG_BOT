"""Сервис пользовательских рейтингов."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import ratings as rating_repository


class RatingsService:
    """Бизнес-сценарии для пользовательских рейтингов."""

    update_or_create_user_exercise_rating = staticmethod(
        rating_repository.update_or_create_user_exercise_rating
    )
    has_rating_for_training_user_and_exercise = staticmethod(
        rating_repository.has_rating_for_training_user_and_exercise
    )


StatisticData = rating_repository.StatisticData


async def update_or_create_user_exercise_rating(
    session: AsyncSession,
    user_id: int,
) -> None:
    """Обновляет рейтинги пользователя.

    Позже этот сценарий будет ставить задачу в worker, а не выполнять пересчет синхронно.
    """
    await rating_repository.update_or_create_user_exercise_rating(session, user_id)


async def has_rating_for_training_user_and_exercise(
    session: AsyncSession,
    training_id: int,
    exercise_id: int,
) -> bool:
    """Проверяет, есть ли рейтинг для пользователя тренировки и упражнения."""
    return await rating_repository.has_rating_for_training_user_and_exercise(
        session,
        training_id,
        exercise_id,
    )
